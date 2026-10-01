"""Bounded command execution with descendant cleanup.

Adapted from this repository's eval.live containment: suspend before
assigning a Windows Job, then resume. Adds bounded disk-spooled output and
cleanup on every exit path. POSIX process groups are lifecycle management,
not an escape-resistant sandbox: a descendant can deliberately leave a group.
"""
from __future__ import annotations

from contextlib import contextmanager
import math
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import time


MAX_OUTPUT_BYTES = 8 * 1024 * 1024
_POLL_SECONDS = .01


class OutputLimitExceeded(subprocess.SubprocessError):
    """The command's combined output cannot be accepted without truncation."""

    def __init__(self, command: str | list[str], stdout: str = "", stderr: str = ""):
        self.cmd = command
        self.limit = MAX_OUTPUT_BYTES
        self.stdout = self.output = stdout
        self.stderr = stderr
        super().__init__(f"command output exceeded {self.limit} bytes; output is incomplete")


def run(command: str | list[str], *, cwd: Path, timeout: float,
        shell: bool = True, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    """Return status and UTF-8 replacement-decoded stdout/stderr, or raise.

    A timeout raises TimeoutExpired with captured strings. Output above 8 MiB
    combined raises OutputLimitExceeded, including if the parent exited zero.
    Capture uses temporary files, so Python memory is bounded; files can exceed
    the limit between 10 ms polls and are removed after cleanup. Neither timeout
    nor the output cap is an operating-system resource or security boundary.
    Main-thread default SIGTERM becomes SystemExit(143), allowing cleanup; custom
    signal handlers are preserved. Abrupt POSIX host termination (e.g. SIGKILL)
    cannot execute cleanup. Lists with shell=True retain Popen's platform-specific
    semantics.
    """
    if not math.isfinite(timeout):
        raise ValueError("timeout must be finite")
    started = time.monotonic()
    with _cleanup_on_sigterm(), tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        job = _WindowsJob() if os.name == "nt" else None
        child = None
        timed_out = False
        try:
            options = ({"creationflags": 0x00000004 | subprocess.CREATE_NO_WINDOW}
                       if job else {"start_new_session": True})
            child = subprocess.Popen(command, cwd=cwd, shell=shell,
                                     stdin=subprocess.DEVNULL, stdout=out,
                                     stderr=err, env=env, **options)
            if job:
                job.bind(child)
                job.resume(child.pid)
            while True:
                _check_output(command, out, err)
                if child.poll() is not None:
                    break
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    timed_out = True
                    break
                time.sleep(min(_POLL_SECONDS, remaining))
        finally:
            # Cleanup also follows a normal parent exit: inherited file handles
            # and orphaned grandchildren must not keep running after verification.
            try:
                if job:
                    job.close()
                elif child:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            finally:
                if child:
                    if child.poll() is None:
                        child.kill()  # Also handles a failed Windows assignment.
                    child.wait()
        _check_output(command, out, err)
        stdout, stderr = _read(out), _read(err)
        if timed_out:
            raise subprocess.TimeoutExpired(command, timeout, stdout, stderr)
        return subprocess.CompletedProcess(command, child.returncode, stdout, stderr)


def _check_output(command, out, err) -> None:
    if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > MAX_OUTPUT_BYTES:
        # Keep a bounded excerpt from both channels, so noisy stdout cannot
        # erase the diagnostic printed on stderr. The exception is never success.
        raise OutputLimitExceeded(command, _read(out, MAX_OUTPUT_BYTES // 2),
                                  _read(err, MAX_OUTPUT_BYTES // 2))


def _read(stream, limit: int = MAX_OUTPUT_BYTES + 1) -> str:
    stream.seek(0)
    # Bounded even if a POSIX descendant escaped its process group and kept
    # writing after the final size check. A short read is never silently accepted.
    data = stream.read(limit)
    if len(data) > MAX_OUTPUT_BYTES:
        raise OutputLimitExceeded("captured stream")
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


@contextmanager
def _cleanup_on_sigterm():
    """Let the main thread unwind on ordinary termination, then restore policy."""
    install = (threading.current_thread() is threading.main_thread()
               and signal.getsignal(signal.SIGTERM) == signal.SIG_DFL)

    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    if install:
        signal.signal(signal.SIGTERM, terminate)
    try:
        yield
    finally:
        if install:
            signal.signal(signal.SIGTERM, signal.SIG_DFL)


class _WindowsJob:
    """Kill-on-close Job created before any command can execute."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        self.lib = lib = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": (wintypes.HANDLE, [wintypes.LPVOID, wintypes.LPCWSTR]),
            "SetInformationJobObject": (wintypes.BOOL, [wintypes.HANDLE, ctypes.c_int,
                                                        wintypes.LPVOID, wintypes.DWORD]),
            "QueryInformationJobObject": (wintypes.BOOL, [wintypes.HANDLE, ctypes.c_int,
                                                          wintypes.LPVOID, wintypes.DWORD,
                                                          wintypes.LPVOID]),
            "AssignProcessToJobObject": (wintypes.BOOL, [wintypes.HANDLE, wintypes.HANDLE]),
            "IsProcessInJob": (wintypes.BOOL, [wintypes.HANDLE, wintypes.HANDLE,
                                               ctypes.POINTER(wintypes.BOOL)]),
            "TerminateJobObject": (wintypes.BOOL, [wintypes.HANDLE, wintypes.UINT]),
            "CloseHandle": (wintypes.BOOL, [wintypes.HANDLE]),
            "OpenThread": (wintypes.HANDLE, [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]),
            "ResumeThread": (wintypes.DWORD, [wintypes.HANDLE]),
            "CreateToolhelp32Snapshot": (wintypes.HANDLE, [wintypes.DWORD, wintypes.DWORD]),
        }
        for name, (result, args) in signatures.items():
            function = getattr(lib, name)
            function.restype, function.argtypes = result, args

        class Limits(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                        ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class Extended(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", Limits), ("IoInfo", ctypes.c_uint64 * 6),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        self.handle = lib.CreateJobObjectW(None, None)
        if not self.handle:
            raise self._error("CreateJobObjectW")
        info = Extended()
        info.BasicLimitInformation.LimitFlags = 0x2000
        if not lib.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            error = self._error("SetInformationJobObject")
            lib.CloseHandle(self.handle)
            self.handle = None
            raise error

    @staticmethod
    def _error(operation):
        import ctypes
        return OSError(f"cannot contain command: {operation} failed (Windows error "
                       f"{ctypes.get_last_error()})")

    def bind(self, child):
        import ctypes
        from ctypes import wintypes
        if not self.lib.AssignProcessToJobObject(self.handle, int(child._handle)):
            raise self._error("AssignProcessToJobObject")
        inside = wintypes.BOOL()
        if not self.lib.IsProcessInJob(int(child._handle), self.handle, ctypes.byref(inside)):
            raise self._error("IsProcessInJob")
        if not inside.value:
            raise OSError("cannot contain command: Job membership check failed")

    def resume(self, pid):
        import ctypes
        from ctypes import wintypes

        class Entry(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                        ("th32ThreadID", wintypes.DWORD), ("th32OwnerProcessID", wintypes.DWORD),
                        ("tpBasePri", wintypes.LONG), ("tpDeltaPri", wintypes.LONG),
                        ("dwFlags", wintypes.DWORD)]

        lib = self.lib
        for name in ("Thread32First", "Thread32Next"):
            getattr(lib, name).argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
            getattr(lib, name).restype = wintypes.BOOL
        snapshot = lib.CreateToolhelp32Snapshot(4, 0)
        if not snapshot or snapshot == ctypes.c_void_p(-1).value:
            raise self._error("CreateToolhelp32Snapshot")
        entry = Entry()
        entry.dwSize = ctypes.sizeof(entry)
        try:
            more = lib.Thread32First(snapshot, ctypes.byref(entry))
            while more:
                if entry.th32OwnerProcessID == pid:
                    thread = lib.OpenThread(0x0002, False, entry.th32ThreadID)
                    if not thread:
                        raise self._error("OpenThread")
                    try:
                        if lib.ResumeThread(thread) == 0xFFFFFFFF:
                            raise self._error("ResumeThread")
                        return
                    finally:
                        lib.CloseHandle(thread)
                more = lib.Thread32Next(snapshot, ctypes.byref(entry))
            raise OSError("cannot contain command: suspended thread was not found")
        finally:
            lib.CloseHandle(snapshot)

    def close(self):
        import ctypes
        from ctypes import wintypes

        class Accounting(ctypes.Structure):
            _fields_ = [("Times", ctypes.c_int64 * 4), ("PageFaults", wintypes.DWORD),
                        ("TotalProcesses", wintypes.DWORD), ("ActiveProcesses", wintypes.DWORD),
                        ("TerminatedProcesses", wintypes.DWORD)]

        if not self.handle:
            return
        try:
            if not self.lib.TerminateJobObject(self.handle, 1):
                raise self._error("TerminateJobObject")
            deadline = time.monotonic() + 5
            while True:
                info = Accounting()
                if not self.lib.QueryInformationJobObject(self.handle, 1, ctypes.byref(info),
                                                          ctypes.sizeof(info), None):
                    raise self._error("QueryInformationJobObject")
                if not info.ActiveProcesses:
                    break
                if time.monotonic() >= deadline:
                    raise OSError("command Job did not terminate within five seconds")
                time.sleep(_POLL_SECONDS)
        finally:
            self.lib.CloseHandle(self.handle)
            self.handle = None
