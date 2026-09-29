"""Real-process regressions for bounded verification command execution."""
import importlib
import importlib.util
import inspect
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest


def runner():
    assert importlib.util.find_spec("core.process") is not None, "process runner is missing"
    return importlib.import_module("core.process")


def python(source):
    return [sys.executable, "-c", source]


@pytest.mark.parametrize("status", [0, 7])
def test_returns_status_and_decoded_separate_streams(tmp_path, status):
    done = runner().run(python(
        "import os,sys; os.write(1,b'hello\\r\\n'); "
        "os.write(2,b'bad \\xff\\n'); sys.exit(" + str(status) + ")"
    ), cwd=tmp_path, timeout=10, shell=False)
    assert isinstance(done, subprocess.CompletedProcess)
    assert done.returncode == status
    assert done.stdout == "hello\n"
    assert done.stderr == "bad \ufffd\n"


def test_string_command_uses_shell_and_requested_directory(tmp_path):
    done = runner().run("echo shell-works", cwd=tmp_path, timeout=10)
    assert done.returncode == 0
    assert done.stdout.strip() == "shell-works"
    done = runner().run(python("import os; print(os.getcwd())"),
                        cwd=tmp_path, timeout=10, shell=False)
    assert Path(done.stdout.strip()) == tmp_path


def test_timeout_preserves_output_as_strings(tmp_path):
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        runner().run(python("import time,sys; print('before',flush=True); "
                            "print('error',file=sys.stderr,flush=True); time.sleep(60)"),
                     cwd=tmp_path, timeout=1, shell=False)
    assert caught.value.stdout == "before\n"
    assert caught.value.stderr == "error\n"


def tree_command(tmp_path, linger):
    leaf = tmp_path / "leaf.py"
    leaf.write_text("import os,time,pathlib\n"
                    "pathlib.Path('grandchild.pid').write_text(str(os.getpid()))\n"
                    "time.sleep(60)\n", encoding="utf-8")
    child = tmp_path / "child.py"
    child.write_text("import os,time,pathlib,subprocess,sys\n"
                     "pathlib.Path('child.pid').write_text(str(os.getpid()))\n"
                     "subprocess.Popen([sys.executable,'leaf.py'])\n"
                     "time.sleep(60)\n", encoding="utf-8")
    return python("import os,time,pathlib,subprocess,sys\n"
                  "pathlib.Path('parent.pid').write_text(str(os.getpid()))\n"
                  "subprocess.Popen([sys.executable,'child.py'])\n"
                  "while not pathlib.Path('grandchild.pid').exists(): time.sleep(.01)\n"
                  + ("time.sleep(60)\n" if linger else ""))


def alive(pid):
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x100000, False, pid)
        if not handle:
            return False
        try:
            return kernel.WaitForSingleObject(handle, 0) == 258
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    status = Path(f"/proc/{pid}/stat")
    try:
        return not (status.exists() and status.read_text().rsplit(")", 1)[1].split()[0] in {"Z", "X"})
    except (FileNotFoundError, ProcessLookupError):
        return False  # It exited between the existence probe and the read.


def assert_tree_stopped(tmp_path):
    pids = [int((tmp_path / f"{name}.pid").read_text())
            for name in ("parent", "child", "grandchild")]
    deadline = time.monotonic() + 5
    while any(alive(pid) for pid in pids) and time.monotonic() < deadline:
        time.sleep(.02)
    assert not any(alive(pid) for pid in pids), f"processes survived: {pids}"


@pytest.mark.skipif(os.name == "nt", reason="POSIX proc disappearance")
@pytest.mark.parametrize("error", [FileNotFoundError, ProcessLookupError])
def test_alive_handles_process_disappearing_during_proc_read(monkeypatch, error):
    monkeypatch.setattr(os, "kill", lambda *a: None)
    monkeypatch.setattr(Path, "exists", lambda self: True)
    def vanished(self, *a, **kw):
        raise error()
    monkeypatch.setattr(Path, "read_text", vanished)
    assert not alive(1234)


@pytest.mark.parametrize("linger", [False, True])
def test_stops_child_and_grandchild_after_exit_or_timeout(tmp_path, linger):
    process = runner()
    command = tree_command(tmp_path, linger)
    if linger:
        with pytest.raises(subprocess.TimeoutExpired):
            process.run(command, cwd=tmp_path, timeout=2, shell=False)
    else:
        assert process.run(command, cwd=tmp_path, timeout=10, shell=False).returncode == 0
    assert_tree_stopped(tmp_path)


def test_keyboard_interrupt_cleans_tree_before_reraising(tmp_path, monkeypatch):
    process = runner()
    real_sleep = time.sleep

    def interrupt(delay):
        if (tmp_path / "grandchild.pid").exists():
            raise KeyboardInterrupt
        real_sleep(delay)

    monkeypatch.setattr(process, "time", SimpleNamespace(monotonic=time.monotonic, sleep=interrupt))
    with pytest.raises(KeyboardInterrupt):
        process.run(tree_command(tmp_path, True), cwd=tmp_path, timeout=10, shell=False)
    assert_tree_stopped(tmp_path)


def test_oversized_output_is_explicit_failure(tmp_path):
    process = runner()
    with pytest.raises(process.OutputLimitExceeded, match="output") as caught:
        process.run(python("import os; os.write(2,b'failure detail'); "
                           "os.write(1,b'x'*(9*1024*1024))"),
                    cwd=tmp_path, timeout=10, shell=False)
    assert caught.value.stdout.startswith("xxx")
    assert caught.value.stderr == "failure detail"
    assert len(caught.value.stdout) + len(caught.value.stderr) <= 8 * 1024 * 1024


def test_sigterm_cleans_tree_in_main_thread(tmp_path):
    # Isolate signal delivery so a regression cannot terminate the pytest host.
    process = runner()
    command = tree_command(tmp_path, True)
    source = (
        f"import sys; sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r})\n"
        "import os,signal,time\nfrom pathlib import Path\nfrom types import SimpleNamespace\n"
        "from core import process\n"
        + inspect.getsource(alive) + "\n"
        "original_sleep = time.sleep\n"
        "sent = False\n"
        "def interrupt(delay):\n"
        "    global sent\n"
        "    if Path('grandchild.pid').exists() and not sent:\n"
        "        sent = True\n"
        "        signal.raise_signal(signal.SIGTERM)\n"
        "    original_sleep(delay)\n"
        "process.time = SimpleNamespace(monotonic=time.monotonic,sleep=interrupt)\n"
        "try:\n"
        f"    process.run({command!r},cwd=Path.cwd(),timeout=10,shell=False)\n"
        "except SystemExit:\n"
        "    original_sleep(.2)\n"
        "    if not any(alive(int(p.read_text())) for p in Path.cwd().glob('*.pid')):\n"
        "        Path('clean-before-exit').touch()\n"
        "    raise\n"
    )
    # The outer runner gives even the deliberately broken inner implementation
    # a containment boundary, so this regression does not leak test processes.
    done = process.run(python(source), cwd=tmp_path, timeout=15, shell=False)
    assert done.returncode == 128 + signal.SIGTERM
    assert (tmp_path / "clean-before-exit").exists(), done.stderr
    assert_tree_stopped(tmp_path)


@pytest.mark.parametrize("timeout", [float("nan"), float("inf")])
def test_nonfinite_timeout_cannot_disable_deadline(tmp_path, timeout):
    with pytest.raises(ValueError, match="finite"):
        runner().run(python("print('ran')"), cwd=tmp_path, timeout=timeout, shell=False)


def test_launch_errors_are_not_success(tmp_path):
    with pytest.raises(OSError):
        runner().run([str(tmp_path / "nonexistent-program")],
                     cwd=tmp_path, timeout=1, shell=False)


@pytest.mark.skipif(os.name != "nt", reason="Windows containment setup")
def test_job_failure_refuses_to_execute_command(tmp_path, monkeypatch):
    process = runner()

    def unavailable(self, child):
        raise OSError("job containment unavailable")

    monkeypatch.setattr(process._WindowsJob, "bind", unavailable)
    with pytest.raises(OSError, match="containment unavailable"):
        process.run(python("from pathlib import Path; Path('executed').touch()"),
                    cwd=tmp_path, timeout=10, shell=False)
    assert not (tmp_path / "executed").exists()
