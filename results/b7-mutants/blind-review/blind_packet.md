# Blind review packet — 27 mutants

Classify each mutant. A mutant is the original code with ONE small change
(shown as `original  ->  mutated`). The line marked `>>` is where it was made.

  EQUIVALENT  - no input, call sequence or environment could make the mutated
                program behave observably differently from the original.
  TRIVIAL     - behaviour can differ, but only in a way no reasonable caller or
                user would care about (message wording, a warning's stacklevel,
                performance, a value nothing reads).
  MEANINGFUL  - some reachable input produces observably different behaviour a
                caller or user would care about: a wrong result, a crash, a
                missing side effect, a different exception, a changed default.
  UNSURE      - you cannot decide from the code shown.

Judge from the code alone. Give one short sentence of reasoning per item.

## M01  (src/jinja2/filters.py, operator: return None)
Mutation at line 1431:  `return environment.undefined(obj=obj, name=name)  ->  return None`

```python
   1412 | def do_attr(
   1413 |     environment: "Environment", obj: t.Any, name: str
   1414 | ) -> t.Union[Undefined, t.Any]:
   1415 |     """Get an attribute of an object. ``foo|attr("bar")`` works like
   1416 |     ``foo.bar``, but returns undefined instead of falling back to ``foo["bar"]``
   1417 |     if the attribute doesn't exist.
   1418 | 
   1419 |     See :ref:`Notes on subscriptions <notes-on-subscriptions>` for more details.
   1420 |     """
   1421 |     # Environment.getattr will fall back to obj[name] if obj.name doesn't exist.
   1422 |     # But we want to call env.getattr to get behavior such as sandboxing.
   1423 |     # Determine if the attr exists first, so we know the fallback won't trigger.
   1424 |     try:
   1425 |         # This avoids executing properties/descriptors, but misses __getattr__
   1426 |         # and __getattribute__ dynamic attrs.
   1427 |         getattr_static(obj, name)
   1428 |     except AttributeError:
   1429 |         # This finds dynamic attrs, and we know it's not a descriptor at this point.
   1430 |         if not hasattr(obj, name):
>> 1431 |             return environment.undefined(obj=obj, name=name)
   1432 | 
   1433 |     return environment.getattr(obj, name)
```

## M02  (src/click/_termui_impl.py, operator: delete statement)
Mutation at line 489:  `with _nullpager(stdout, color) as rv:  ->  pass`

```python
    470 | def _pipepager(
    471 |     cmd_parts: list[str], color: bool | None = None
    472 | ) -> t.Iterator[tuple[t.BinaryIO | t.TextIO, str, bool]]:
    473 |     """Page through text by feeding it to another program.
    474 | 
    475 |     Invokes the pager via :class:`subprocess.Popen` with an ``argv`` list
    476 |     produced by :func:`shlex.split`. The command is resolved to an absolute
    477 |     path with :func:`shutil.which` as recommended by the
    478 |     :mod:`subprocess` docs for Windows compatibility.
    479 | 
    480 |     Invoking a pager through this might support colors: if piping to
    481 |     ``less`` and the user hasn't decided on colors, ``LESS=-R`` is set
    482 |     automatically.
    483 |     """
    484 |     # Split the command into the invoked CLI and its parameters.
    485 |     if not cmd_parts:
    486 |         # No usable pager: fall back to stdout through _nullpager so it gets the
    487 |         # same borrowed-stream handling and the caller's stream is not closed.
    488 |         stdout = _default_text_stdout() or StringIO()
>>  489 |         with _nullpager(stdout, color) as rv:
    490 |             yield rv
    491 |         return
    492 | 
    493 |     import shutil
    494 | 
    495 |     cmd = cmd_parts[0]
    496 |     cmd_params = cmd_parts[1:]
    497 | 
    498 |     cmd_filepath = shutil.which(cmd)
    499 |     if not cmd_filepath:
    500 |         # No usable pager: fall back to stdout through _nullpager so it gets the
    501 |         # same borrowed-stream handling and the caller's stream is not closed.
    502 |         stdout = _default_text_stdout() or StringIO()
    503 |         with _nullpager(stdout, color) as rv:
    504 |             yield rv
    505 |         return
    506 | 
    507 |     # Produces a normalized absolute path string.
    508 |     # multi-call binaries such as busybox derive their identity from the symlink
    509 |     # less -> busybox. resolve() causes them to misbehave. (eg. less becomes busybox)
    510 |     cmd_path = Path(cmd_filepath).absolute()
    511 |     cmd_name = cmd_path.name
    512 | 
    513 |     import subprocess
    514 | 
    515 |     # Make a local copy of the environment to not affect the global one.
    516 |     env = dict(os.environ)
    517 | 
    518 |     # If we're piping to less and the user hasn't decided on colors, we enable
    519 |     # them by default we find the -R flag in the command line arguments.
```

## M03  (src/click/_textwrap.py, operator: delete statement)
Mutation at line 29:  `continue  ->  pass`

```python
     11 | def _truncate_visible(text: str, n: int) -> str:
     12 |     """Return the longest prefix of ``text`` containing at most ``n`` visible
     13 |     characters.
     14 | 
     15 |     ANSI escape sequences inside the prefix are kept intact and do not count
     16 |     toward the visible width. A cut is never placed inside an escape sequence.
     17 |     """
     18 |     if n <= 0:
     19 |         return ""
     20 | 
     21 |     visible = 0
     22 |     i = 0
     23 |     cut = 0
     24 |     end = len(text)
     25 |     while i < end:
     26 |         m = _ansi_re.match(text, i)
     27 |         if m is not None:
     28 |             i = m.end()
>>   29 |             continue
     30 |         visible += 1
     31 |         i += 1
     32 |         cut = i
     33 |         if visible >= n:
     34 |             break
     35 |     return text[:cut]
```

## M04  (src/click/core.py, operator: delete statement)
Mutation at line 3280:  `return value  ->  pass`

```python
   3268 |     def process_value(self, ctx: Context, value: t.Any) -> t.Any:
   3269 |         # process_value has to be overridden on Options in order to capture
   3270 |         # `value == UNSET` cases before `type_cast_value()` gets called.
   3271 |         #
   3272 |         # Refs:
   3273 |         # https://github.com/pallets/click/issues/3069
   3274 |         if self.is_flag and not self.required and self.is_bool_flag and value is UNSET:
   3275 |             value = False
   3276 | 
   3277 |             if self.callback is not None:
   3278 |                 value = self.callback(ctx, self, value)
   3279 | 
>> 3280 |             return value
   3281 | 
   3282 |         # in the normal case, rely on Parameter.process_value
   3283 |         return super().process_value(ctx, value)
```

## M05  (src/click/decorators.py, operator: delete statement)
Mutation at line 596:  `kwargs.setdefault('expose_value', False)  ->  pass`

```python
    561 | def custom_version_option(
    562 |     callback: t.Callable[[Context], str],
    563 |     *param_decls: str,
    564 |     **kwargs: t.Any,
    565 | ) -> t.Callable[[FC], FC]:
    566 |     """Add a ``--version`` option whose output is produced by ``callback``.
    567 | 
    568 |     This is the customizable companion to :func:`version_option`. Where
    569 |     :func:`version_option` is intentionally limited to a fixed message and
    570 |     a small set of values, this option calls ``callback`` to build the
    571 |     whole string to print. Use it when you need values that
    572 |     :func:`version_option` does not expose, such as a file path, the
    573 |     Python version, or git metadata.
    574 | 
    575 |     :param callback: Called with the current :class:`Context` when the
    576 |         option is invoked. Its return value is printed, then the program
    577 |         exits.
    578 |     :param param_decls: One or more option names. Defaults to the single
    579 |         value ``--version``.
    580 |     :param kwargs: Extra arguments are passed to :func:`option`.
    581 | 
    582 |     .. versionadded:: 8.5.0
    583 |     """
    584 | 
    585 |     def show_version(ctx: Context, param: Parameter, value: bool) -> None:
    586 |         if not value or ctx.resilient_parsing:
    587 |             return
    588 | 
    589 |         echo(callback(ctx), color=ctx.color)
    590 |         ctx.exit()
    591 | 
    592 |     if not param_decls:
    593 |         param_decls = ("--version",)
    594 | 
    595 |     kwargs.setdefault("is_flag", True)
>>  596 |     kwargs.setdefault("expose_value", False)
    597 |     kwargs.setdefault("is_eager", True)
    598 |     kwargs.setdefault("help", _("Show the version and exit."))
    599 |     kwargs["callback"] = show_version
    600 |     return option(*param_decls, **kwargs)
```

## M06  (src/jinja2/filters.py, operator: delete statement)
Mutation at line 1431:  `return environment.undefined(obj=obj, name=name)  ->  pass`

```python
   1412 | def do_attr(
   1413 |     environment: "Environment", obj: t.Any, name: str
   1414 | ) -> t.Union[Undefined, t.Any]:
   1415 |     """Get an attribute of an object. ``foo|attr("bar")`` works like
   1416 |     ``foo.bar``, but returns undefined instead of falling back to ``foo["bar"]``
   1417 |     if the attribute doesn't exist.
   1418 | 
   1419 |     See :ref:`Notes on subscriptions <notes-on-subscriptions>` for more details.
   1420 |     """
   1421 |     # Environment.getattr will fall back to obj[name] if obj.name doesn't exist.
   1422 |     # But we want to call env.getattr to get behavior such as sandboxing.
   1423 |     # Determine if the attr exists first, so we know the fallback won't trigger.
   1424 |     try:
   1425 |         # This avoids executing properties/descriptors, but misses __getattr__
   1426 |         # and __getattribute__ dynamic attrs.
   1427 |         getattr_static(obj, name)
   1428 |     except AttributeError:
   1429 |         # This finds dynamic attrs, and we know it's not a descriptor at this point.
   1430 |         if not hasattr(obj, name):
>> 1431 |             return environment.undefined(obj=obj, name=name)
   1432 | 
   1433 |     return environment.getattr(obj, name)
```

## M07  (src/click/_termui_impl.py, operator: delete statement)
Mutation at line 596:  `yield rv  ->  pass`

```python
    580 | def _tempfilepager(
    581 |     cmd_parts: list[str], color: bool | None = None
    582 | ) -> t.Iterator[tuple[t.BinaryIO | t.TextIO, str, bool]]:
    583 |     """Page through text by invoking a program on a temporary file.
    584 | 
    585 |     Used as the primary pager strategy on Windows (where piping to
    586 |     ``more`` adds spurious ``\\r\\n``), and as a fallback on other
    587 |     platforms. The command is resolved to an absolute path with
    588 |     :func:`shutil.which`.
    589 |     """
    590 |     # Split the command into the invoked CLI and its parameters.
    591 |     if not cmd_parts:
    592 |         # No usable pager: fall back to stdout through _nullpager so it gets the
    593 |         # same borrowed-stream handling and the caller's stream is not closed.
    594 |         stdout = _default_text_stdout() or StringIO()
    595 |         with _nullpager(stdout, color) as rv:
>>  596 |             yield rv
    597 |         return
    598 | 
    599 |     import shutil
    600 |     import subprocess
    601 | 
    602 |     cmd = cmd_parts[0]
    603 | 
    604 |     cmd_filepath = shutil.which(cmd)
    605 |     if not cmd_filepath:
    606 |         # No usable pager: fall back to stdout through _nullpager so it gets the
    607 |         # same borrowed-stream handling and the caller's stream is not closed.
    608 |         stdout = _default_text_stdout() or StringIO()
    609 |         with _nullpager(stdout, color) as rv:
    610 |             yield rv
    611 |         return
    612 | 
    613 |     # Produces a normalized absolute path string.
    614 |     # multi-call binaries such as busybox derive their identity from the symlink
    615 |     # less -> busybox. resolve() causes them to misbehave. (eg. less becomes busybox)
    616 |     cmd_path = Path(cmd_filepath).absolute()
    617 | 
    618 |     import tempfile
    619 | 
    620 |     encoding = get_best_encoding(sys.stdout)
    621 |     if color is None:
    622 |         color = False
    623 |     # On Windows, NamedTemporaryFile cannot be opened by another process
    624 |     # while Python still has it open, so we use delete=False and clean up manually
    625 |     # rather than using a contextmanager here.
    626 |     f = tempfile.NamedTemporaryFile(mode="wb", delete=False)
    627 |     try:
    628 |         yield t.cast(t.BinaryIO, f), encoding, color
    629 |         f.flush()
    630 |         f.close()
    631 |         subprocess.call([str(cmd_path), f.name])
    632 |     finally:
    633 |         os.unlink(f.name)
```

## M08  (src/click/decorators.py, operator: delete statement)
Mutation at line 590:  `ctx.exit()  ->  pass`

```python
    585 |     def show_version(ctx: Context, param: Parameter, value: bool) -> None:
    586 |         if not value or ctx.resilient_parsing:
    587 |             return
    588 | 
    589 |         echo(callback(ctx), color=ctx.color)
>>  590 |         ctx.exit()
```

## M09  (src/click/testing.py, operator: delete statement)
Mutation at line 685:  `if fd_out:  ->  pass`

```python
    655 | 
    656 |                 if e_code is None:
    657 |                     e_code = 0
    658 | 
    659 |                 if e_code != 0:
    660 |                     exception = e
    661 | 
    662 |                 if not isinstance(e_code, int):
    663 |                     sys.stdout.write(str(e_code))
    664 |                     sys.stdout.write("\n")
    665 |                     e_code = 1
    666 | 
    667 |                 exit_code = e_code
    668 | 
    669 |             except Exception as e:
    670 |                 if not catch_exceptions:
    671 |                     raise
    672 |                 exception = e
    673 |                 exit_code = 1
    674 |                 exc_info = sys.exc_info()
    675 |             finally:
    676 |                 sys.stdout.flush()
    677 |                 sys.stderr.flush()
    678 | 
    679 |                 # Stop fd capture and merge the captured bytes into
    680 |                 # the stdout/stderr BytesIO streams. BytesIOCopy mirrors
    681 |                 # those writes into outstreams[2] automatically.
    682 |                 if cap_out is not None and cap_err is not None:
    683 |                     fd_out = cap_out.stop()
    684 |                     fd_err = cap_err.stop()
>>  685 |                     if fd_out:
    686 |                         outstreams[0].write(fd_out)
    687 |                     if fd_err:
    688 |                         outstreams[1].write(fd_err)
    689 | 
    690 |                 stdout = outstreams[0].getvalue()
    691 |                 stderr = outstreams[1].getvalue()
    692 |                 output = outstreams[2].getvalue()
    693 | 
    694 |         return Result(
    695 |             runner=self,
    696 |             stdout_bytes=stdout,
    697 |             stderr_bytes=stderr,
    698 |             output_bytes=output,
    699 |             return_value=return_value,
    700 |             exit_code=exit_code,
    701 |             exception=exception,
    702 |             exc_info=exc_info,  # type: ignore
    703 |         )
```

## M10  (src/jinja2/filters.py, operator: negate condition)
Mutation at line 1430:  `if not hasattr(obj, name):  ->  if not not hasattr(obj, name):`

```python
   1412 | def do_attr(
   1413 |     environment: "Environment", obj: t.Any, name: str
   1414 | ) -> t.Union[Undefined, t.Any]:
   1415 |     """Get an attribute of an object. ``foo|attr("bar")`` works like
   1416 |     ``foo.bar``, but returns undefined instead of falling back to ``foo["bar"]``
   1417 |     if the attribute doesn't exist.
   1418 | 
   1419 |     See :ref:`Notes on subscriptions <notes-on-subscriptions>` for more details.
   1420 |     """
   1421 |     # Environment.getattr will fall back to obj[name] if obj.name doesn't exist.
   1422 |     # But we want to call env.getattr to get behavior such as sandboxing.
   1423 |     # Determine if the attr exists first, so we know the fallback won't trigger.
   1424 |     try:
   1425 |         # This avoids executing properties/descriptors, but misses __getattr__
   1426 |         # and __getattribute__ dynamic attrs.
   1427 |         getattr_static(obj, name)
   1428 |     except AttributeError:
   1429 |         # This finds dynamic attrs, and we know it's not a descriptor at this point.
>> 1430 |         if not hasattr(obj, name):
   1431 |             return environment.undefined(obj=obj, name=name)
   1432 | 
   1433 |     return environment.getattr(obj, name)
```

## M11  (src/click/decorators.py, operator: const True->False)
Mutation at line 597:  `kwargs.setdefault('is_eager', True)  ->  kwargs.setdefault('is_eager', False)`

```python
    561 | def custom_version_option(
    562 |     callback: t.Callable[[Context], str],
    563 |     *param_decls: str,
    564 |     **kwargs: t.Any,
    565 | ) -> t.Callable[[FC], FC]:
    566 |     """Add a ``--version`` option whose output is produced by ``callback``.
    567 | 
    568 |     This is the customizable companion to :func:`version_option`. Where
    569 |     :func:`version_option` is intentionally limited to a fixed message and
    570 |     a small set of values, this option calls ``callback`` to build the
    571 |     whole string to print. Use it when you need values that
    572 |     :func:`version_option` does not expose, such as a file path, the
    573 |     Python version, or git metadata.
    574 | 
    575 |     :param callback: Called with the current :class:`Context` when the
    576 |         option is invoked. Its return value is printed, then the program
    577 |         exits.
    578 |     :param param_decls: One or more option names. Defaults to the single
    579 |         value ``--version``.
    580 |     :param kwargs: Extra arguments are passed to :func:`option`.
    581 | 
    582 |     .. versionadded:: 8.5.0
    583 |     """
    584 | 
    585 |     def show_version(ctx: Context, param: Parameter, value: bool) -> None:
    586 |         if not value or ctx.resilient_parsing:
    587 |             return
    588 | 
    589 |         echo(callback(ctx), color=ctx.color)
    590 |         ctx.exit()
    591 | 
    592 |     if not param_decls:
    593 |         param_decls = ("--version",)
    594 | 
    595 |     kwargs.setdefault("is_flag", True)
    596 |     kwargs.setdefault("expose_value", False)
>>  597 |     kwargs.setdefault("is_eager", True)
    598 |     kwargs.setdefault("help", _("Show the version and exit."))
    599 |     kwargs["callback"] = show_version
    600 |     return option(*param_decls, **kwargs)
```

## M12  (src/click/_textwrap.py, operator: delete statement)
Mutation at line 149:  `del cur_line[-1]  ->  pass`

```python
    119 |                 self._handle_long_word(chunks, cur_line, cur_len, width)
    120 |                 cur_len = sum(map(term_len, cur_line))
    121 | 
    122 |             if self.drop_whitespace and cur_line and cur_line[-1].strip() == "":
    123 |                 cur_len -= term_len(cur_line[-1])
    124 |                 del cur_line[-1]
    125 | 
    126 |             if cur_line:
    127 |                 if (
    128 |                     self.max_lines is None
    129 |                     or len(lines) + 1 < self.max_lines
    130 |                     or (
    131 |                         not chunks
    132 |                         or self.drop_whitespace
    133 |                         and len(chunks) == 1
    134 |                         and not chunks[0].strip()
    135 |                     )
    136 |                     and cur_len <= width
    137 |                 ):
    138 |                     lines.append(indent + "".join(cur_line))
    139 |                 else:
    140 |                     while cur_line:
    141 |                         if (
    142 |                             cur_line[-1].strip()
    143 |                             and cur_len + term_len(self.placeholder) <= width
    144 |                         ):
    145 |                             cur_line.append(self.placeholder)
    146 |                             lines.append(indent + "".join(cur_line))
    147 |                             break
    148 |                         cur_len -= term_len(cur_line[-1])
>>  149 |                         del cur_line[-1]
    150 |                     else:
    151 |                         if lines:
    152 |                             prev_line = lines[-1].rstrip()
    153 |                             if (
    154 |                                 term_len(prev_line) + term_len(self.placeholder)
    155 |                                 <= self.width
    156 |                             ):
    157 |                                 lines[-1] = prev_line + self.placeholder
    158 |                                 break
    159 |                         lines.append(indent + self.placeholder.lstrip())
    160 |                     break
    161 | 
    162 |         return lines
```

## M13  (src/click/_termui_impl.py, operator: delete statement)
Mutation at line 595:  `with _nullpager(stdout, color) as rv:  ->  pass`

```python
    580 | def _tempfilepager(
    581 |     cmd_parts: list[str], color: bool | None = None
    582 | ) -> t.Iterator[tuple[t.BinaryIO | t.TextIO, str, bool]]:
    583 |     """Page through text by invoking a program on a temporary file.
    584 | 
    585 |     Used as the primary pager strategy on Windows (where piping to
    586 |     ``more`` adds spurious ``\\r\\n``), and as a fallback on other
    587 |     platforms. The command is resolved to an absolute path with
    588 |     :func:`shutil.which`.
    589 |     """
    590 |     # Split the command into the invoked CLI and its parameters.
    591 |     if not cmd_parts:
    592 |         # No usable pager: fall back to stdout through _nullpager so it gets the
    593 |         # same borrowed-stream handling and the caller's stream is not closed.
    594 |         stdout = _default_text_stdout() or StringIO()
>>  595 |         with _nullpager(stdout, color) as rv:
    596 |             yield rv
    597 |         return
    598 | 
    599 |     import shutil
    600 |     import subprocess
    601 | 
    602 |     cmd = cmd_parts[0]
    603 | 
    604 |     cmd_filepath = shutil.which(cmd)
    605 |     if not cmd_filepath:
    606 |         # No usable pager: fall back to stdout through _nullpager so it gets the
    607 |         # same borrowed-stream handling and the caller's stream is not closed.
    608 |         stdout = _default_text_stdout() or StringIO()
    609 |         with _nullpager(stdout, color) as rv:
    610 |             yield rv
    611 |         return
    612 | 
    613 |     # Produces a normalized absolute path string.
    614 |     # multi-call binaries such as busybox derive their identity from the symlink
    615 |     # less -> busybox. resolve() causes them to misbehave. (eg. less becomes busybox)
    616 |     cmd_path = Path(cmd_filepath).absolute()
    617 | 
    618 |     import tempfile
    619 | 
    620 |     encoding = get_best_encoding(sys.stdout)
    621 |     if color is None:
    622 |         color = False
    623 |     # On Windows, NamedTemporaryFile cannot be opened by another process
    624 |     # while Python still has it open, so we use delete=False and clean up manually
    625 |     # rather than using a contextmanager here.
    626 |     f = tempfile.NamedTemporaryFile(mode="wb", delete=False)
    627 |     try:
    628 |         yield t.cast(t.BinaryIO, f), encoding, color
    629 |         f.flush()
    630 |         f.close()
    631 |         subprocess.call([str(cmd_path), f.name])
    632 |     finally:
    633 |         os.unlink(f.name)
```

## M14  (src/click/testing.py, operator: delete statement)
Mutation at line 25:  `CaptureMode = t.Literal['sys', 'fd']  ->  pass`

```python
     10 | import tempfile
     11 | import typing as t
     12 | from types import TracebackType
     13 | 
     14 | from . import _compat
     15 | from . import formatting
     16 | from . import termui
     17 | from . import utils
     18 | from ._compat import _find_binary_reader
     19 | 
     20 | if t.TYPE_CHECKING:
     21 |     from _typeshed import ReadableBuffer
     22 | 
     23 |     from .core import Command
     24 | 
>>   25 | CaptureMode = t.Literal["sys", "fd"]
     26 | 
     27 | 
     28 | class EchoingStdin:
     29 |     def __init__(self, input: t.BinaryIO, output: t.BinaryIO) -> None:
     30 |         self._input = input
     31 |         self._output = output
     32 |         self._paused = False
     33 | 
     34 |     def __getattr__(self, x: str) -> t.Any:
     35 |         return getattr(self._input, x)
     36 | 
     37 |     def _echo(self, rv: bytes) -> bytes:
     38 |         if not self._paused:
     39 |             self._output.write(rv)
     40 | 
```

## M15  (src/click/testing.py, operator: string XX)
Mutation at line 94:  `assert self._tmpfile is not None, '_FDCapture.start() was not called'  ->  assert self._tmpfile is not None, 'XX_FDCapture.start() was not called`

```python
     93 |     def stop(self) -> bytes:
>>   94 |         assert self._tmpfile is not None, "_FDCapture.start() was not called"
     95 |         os.dup2(self.saved_fd, self._targetfd)
     96 |         os.close(self.saved_fd)
     97 |         self.saved_fd = -1
     98 |         self._tmpfile.seek(0)
     99 |         data = self._tmpfile.read()
    100 |         self._tmpfile.close()
    101 |         self._tmpfile = None
    102 |         return data
```

## M16  (src/click/testing.py, operator: delete statement)
Mutation at line 97:  `self.saved_fd = -1  ->  pass`

```python
     93 |     def stop(self) -> bytes:
     94 |         assert self._tmpfile is not None, "_FDCapture.start() was not called"
     95 |         os.dup2(self.saved_fd, self._targetfd)
     96 |         os.close(self.saved_fd)
>>   97 |         self.saved_fd = -1
     98 |         self._tmpfile.seek(0)
     99 |         data = self._tmpfile.read()
    100 |         self._tmpfile.close()
    101 |         self._tmpfile = None
    102 |         return data
```

## M17  (src/click/_termui_impl.py, operator: delete statement)
Mutation at line 490:  `yield rv  ->  pass`

```python
    470 | def _pipepager(
    471 |     cmd_parts: list[str], color: bool | None = None
    472 | ) -> t.Iterator[tuple[t.BinaryIO | t.TextIO, str, bool]]:
    473 |     """Page through text by feeding it to another program.
    474 | 
    475 |     Invokes the pager via :class:`subprocess.Popen` with an ``argv`` list
    476 |     produced by :func:`shlex.split`. The command is resolved to an absolute
    477 |     path with :func:`shutil.which` as recommended by the
    478 |     :mod:`subprocess` docs for Windows compatibility.
    479 | 
    480 |     Invoking a pager through this might support colors: if piping to
    481 |     ``less`` and the user hasn't decided on colors, ``LESS=-R`` is set
    482 |     automatically.
    483 |     """
    484 |     # Split the command into the invoked CLI and its parameters.
    485 |     if not cmd_parts:
    486 |         # No usable pager: fall back to stdout through _nullpager so it gets the
    487 |         # same borrowed-stream handling and the caller's stream is not closed.
    488 |         stdout = _default_text_stdout() or StringIO()
    489 |         with _nullpager(stdout, color) as rv:
>>  490 |             yield rv
    491 |         return
    492 | 
    493 |     import shutil
    494 | 
    495 |     cmd = cmd_parts[0]
    496 |     cmd_params = cmd_parts[1:]
    497 | 
    498 |     cmd_filepath = shutil.which(cmd)
    499 |     if not cmd_filepath:
    500 |         # No usable pager: fall back to stdout through _nullpager so it gets the
    501 |         # same borrowed-stream handling and the caller's stream is not closed.
    502 |         stdout = _default_text_stdout() or StringIO()
    503 |         with _nullpager(stdout, color) as rv:
    504 |             yield rv
    505 |         return
    506 | 
    507 |     # Produces a normalized absolute path string.
    508 |     # multi-call binaries such as busybox derive their identity from the symlink
    509 |     # less -> busybox. resolve() causes them to misbehave. (eg. less becomes busybox)
    510 |     cmd_path = Path(cmd_filepath).absolute()
    511 |     cmd_name = cmd_path.name
    512 | 
    513 |     import subprocess
    514 | 
    515 |     # Make a local copy of the environment to not affect the global one.
    516 |     env = dict(os.environ)
    517 | 
    518 |     # If we're piping to less and the user hasn't decided on colors, we enable
    519 |     # them by default we find the -R flag in the command line arguments.
    520 |     if color is None and cmd_name == "less":
```

## M18  (src/click/testing.py, operator: delete statement)
Mutation at line 626:  `cap_err.start()  ->  pass`

```python
    596 |         .. versionchanged:: 8.2
    597 |             The result object always returns the ``stderr_bytes`` stream.
    598 | 
    599 |         .. versionchanged:: 8.0
    600 |             The result object has the ``return_value`` attribute with
    601 |             the value returned from the invoked command.
    602 | 
    603 |         .. versionchanged:: 4.0
    604 |             Added the ``color`` parameter.
    605 | 
    606 |         .. versionchanged:: 3.0
    607 |             Added the ``catch_exceptions`` parameter.
    608 | 
    609 |         .. versionchanged:: 3.0
    610 |             The result object has the ``exc_info`` attribute with the
    611 |             traceback if available.
    612 |         """
    613 |         exc_info = None
    614 |         if catch_exceptions is None:
    615 |             catch_exceptions = self.catch_exceptions
    616 | 
    617 |         # Set up fd capture before isolation replaces sys.stdout and sys.stderr.
    618 |         cap_out: _FDCapture | None = None
    619 |         cap_err: _FDCapture | None = None
    620 | 
    621 |         if self.capture == "fd":
    622 |             cap_out = _FDCapture(1)
    623 |             cap_err = _FDCapture(2)
    624 |             try:
    625 |                 cap_out.start()
>>  626 |                 cap_err.start()
    627 |             except OSError:
    628 |                 cap_out = cap_err = None
    629 | 
    630 |         with self.isolation(input=input, env=env, color=color) as outstreams:
    631 |             # Point the captured streams' fileno() at the saved (original)
    632 |             # fd so that C-level consumers like faulthandler keep working
    633 |             # while fd 1/2 are redirected to the capture tmpfile.
    634 |             if cap_out is not None and cap_err is not None:
    635 |                 sys.stdout._original_fd = cap_out.saved_fd  # type: ignore[union-attr]
    636 |                 sys.stderr._original_fd = cap_err.saved_fd  # type: ignore[union-attr]
    637 | 
    638 |             return_value = None
    639 |             exception: BaseException | None = None
    640 |             exit_code = 0
    641 | 
    642 |             if isinstance(args, str):
    643 |                 args = shlex.split(args)
    644 | 
    645 |             try:
    646 |                 prog_name = extra.pop("prog_name")
    647 |             except KeyError:
    648 |                 prog_name = self.get_default_prog_name(cli)
    649 | 
    650 |             try:
    651 |                 return_value = cli.main(args=args or (), prog_name=prog_name, **extra)
    652 |             except SystemExit as e:
    653 |                 exc_info = sys.exc_info()
    654 |                 e_code = t.cast("int | t.Any | None", e.code)
    655 | 
    656 |                 if e_code is None:
```

## M19  (src/click/testing.py, operator: const 3->4)
Mutation at line 780:  `warnings.warn("'isolated_filesystem' is deprecated and will be removed  ->  warnings.warn("'isolated_filesystem' is deprecated and will be removed`

```python
    742 |     def isolated_filesystem(
    743 |         self, temp_dir: str | os.PathLike[str] | None = None
    744 |     ) -> cabc.Generator[str]:
    745 |         """A context manager that creates a temporary directory and
    746 |         changes the current working directory to it. This isolates tests
    747 |         that affect the contents of the CWD to prevent them from
    748 |         interfering with each other.
    749 | 
    750 |         .. warning::
    751 |             This helper predates Python 3 and modern pytest, and is not
    752 |             thread-safe: it relies on :func:`os.chdir`, which mutates
    753 |             process-global state, and :meth:`invoke` swaps the
    754 |             process-global standard streams too. Parallelize tests with
    755 |             processes (``pytest-xdist``), not threads. Locking the
    756 |             runner (:pr:`3511`, :pr:`3520`, :pr:`3530`) and a
    757 |             ``set_filesystem()`` API (:issue:`3123`) were declined:
    758 |             neither removes the global-state mutation. See :issue:`3700`
    759 |             and :issue:`3501`.
    760 | 
    761 |         :param temp_dir: Create the temporary directory under this
    762 |             directory. If given, the created directory is not removed
    763 |             when exiting.
    764 | 
    765 |         .. deprecated:: 8.5.0
    766 |             Will be removed in Click 9.0. Use
    767 |             :class:`tempfile.TemporaryDirectory` or pytest's
    768 |             ``tmp_path`` fixture with absolute paths instead.
    769 | 
    770 |         .. versionchanged:: 8.0
    771 |             Added the ``temp_dir`` parameter.
    772 |         """
    773 |         import warnings
    774 | 
    775 |         warnings.warn(
    776 |             "'isolated_filesystem' is deprecated and will be removed in Click"
    777 |             " 9.0. Use 'tempfile.TemporaryDirectory' or pytest's 'tmp_path'"
    778 |             " fixture with absolute paths instead.",
    779 |             DeprecationWarning,
>>  780 |             stacklevel=3,
    781 |         )
    782 | 
    783 |         cwd = os.getcwd()
    784 |         dt = tempfile.mkdtemp(dir=temp_dir)
    785 |         os.chdir(dt)
    786 | 
    787 |         try:
    788 |             yield dt
    789 |         finally:
    790 |             os.chdir(cwd)
    791 | 
    792 |             if temp_dir is None:
    793 |                 import shutil
    794 | 
    795 |                 try:
    796 |                     shutil.rmtree(dt)
    797 |                 except OSError:
    798 |                     pass
```

## M20  (src/click/core.py, operator: negate condition)
Mutation at line 3277:  `if self.callback is not None:  ->  if not self.callback is not None:`

```python
   3268 |     def process_value(self, ctx: Context, value: t.Any) -> t.Any:
   3269 |         # process_value has to be overridden on Options in order to capture
   3270 |         # `value == UNSET` cases before `type_cast_value()` gets called.
   3271 |         #
   3272 |         # Refs:
   3273 |         # https://github.com/pallets/click/issues/3069
   3274 |         if self.is_flag and not self.required and self.is_bool_flag and value is UNSET:
   3275 |             value = False
   3276 | 
>> 3277 |             if self.callback is not None:
   3278 |                 value = self.callback(ctx, self, value)
   3279 | 
   3280 |             return value
   3281 | 
   3282 |         # in the normal case, rely on Parameter.process_value
   3283 |         return super().process_value(ctx, value)
```

## M21  (src/jinja2/filters.py, operator: delete statement)
Mutation at line 1430:  `if not hasattr(obj, name):  ->  pass`

```python
   1412 | def do_attr(
   1413 |     environment: "Environment", obj: t.Any, name: str
   1414 | ) -> t.Union[Undefined, t.Any]:
   1415 |     """Get an attribute of an object. ``foo|attr("bar")`` works like
   1416 |     ``foo.bar``, but returns undefined instead of falling back to ``foo["bar"]``
   1417 |     if the attribute doesn't exist.
   1418 | 
   1419 |     See :ref:`Notes on subscriptions <notes-on-subscriptions>` for more details.
   1420 |     """
   1421 |     # Environment.getattr will fall back to obj[name] if obj.name doesn't exist.
   1422 |     # But we want to call env.getattr to get behavior such as sandboxing.
   1423 |     # Determine if the attr exists first, so we know the fallback won't trigger.
   1424 |     try:
   1425 |         # This avoids executing properties/descriptors, but misses __getattr__
   1426 |         # and __getattribute__ dynamic attrs.
   1427 |         getattr_static(obj, name)
   1428 |     except AttributeError:
   1429 |         # This finds dynamic attrs, and we know it's not a descriptor at this point.
>> 1430 |         if not hasattr(obj, name):
   1431 |             return environment.undefined(obj=obj, name=name)
   1432 | 
   1433 |     return environment.getattr(obj, name)
```

## M22  (src/click/decorators.py, operator: delete statement)
Mutation at line 587:  `return  ->  pass`

```python
    585 |     def show_version(ctx: Context, param: Parameter, value: bool) -> None:
    586 |         if not value or ctx.resilient_parsing:
>>  587 |             return
    588 | 
    589 |         echo(callback(ctx), color=ctx.color)
    590 |         ctx.exit()
```

## M23  (src/jinja2/filters.py, operator: delete statement)
Mutation at line 1427:  `getattr_static(obj, name)  ->  pass`

```python
   1412 | def do_attr(
   1413 |     environment: "Environment", obj: t.Any, name: str
   1414 | ) -> t.Union[Undefined, t.Any]:
   1415 |     """Get an attribute of an object. ``foo|attr("bar")`` works like
   1416 |     ``foo.bar``, but returns undefined instead of falling back to ``foo["bar"]``
   1417 |     if the attribute doesn't exist.
   1418 | 
   1419 |     See :ref:`Notes on subscriptions <notes-on-subscriptions>` for more details.
   1420 |     """
   1421 |     # Environment.getattr will fall back to obj[name] if obj.name doesn't exist.
   1422 |     # But we want to call env.getattr to get behavior such as sandboxing.
   1423 |     # Determine if the attr exists first, so we know the fallback won't trigger.
   1424 |     try:
   1425 |         # This avoids executing properties/descriptors, but misses __getattr__
   1426 |         # and __getattribute__ dynamic attrs.
>> 1427 |         getattr_static(obj, name)
   1428 |     except AttributeError:
   1429 |         # This finds dynamic attrs, and we know it's not a descriptor at this point.
   1430 |         if not hasattr(obj, name):
   1431 |             return environment.undefined(obj=obj, name=name)
   1432 | 
   1433 |     return environment.getattr(obj, name)
```

## M24  (src/itsdangerous/timed.py, operator: delete statement)
Mutation at line 126:  `s = want_bytes(s)  ->  pass`

```python
    118 |     def loads(self, s, max_age=None, return_timestamp=False, salt=None):
    119 |         """Reverse of :meth:`dumps`, raises :exc:`.BadSignature` if the
    120 |         signature validation fails. If a ``max_age`` is provided it will
    121 |         ensure the signature is not older than that time in seconds. In
    122 |         case the signature is outdated, :exc:`.SignatureExpired` is
    123 |         raised. All arguments are forwarded to the signer's
    124 |         :meth:`~TimestampSigner.unsign` method.
    125 |         """
>>  126 |         s = want_bytes(s)
    127 |         last_exception = None
    128 |         for signer in self.iter_unsigners(salt):
    129 |             try:
    130 |                 base64d, timestamp = signer.unsign(
    131 |                     s, max_age, return_timestamp=True
    132 |                 )
    133 |                 payload = self.load_payload(base64d)
    134 |                 if return_timestamp:
    135 |                     return payload, timestamp
    136 |                 return payload
    137 |             except BadSignature as err:
    138 |                 last_exception = err
    139 |         raise last_exception
```

## M25  (src/click/_textwrap.py, operator: const 1->2)
Mutation at line 129:  `if self.max_lines is None or len(lines) + 1 < self.max_lines or ((not   ->  if self.max_lines is None or len(lines) + 2 < self.max_lines or ((not `

```python
     99 |                 indent = self.subsequent_indent
    100 |             else:
    101 |                 indent = self.initial_indent
    102 | 
    103 |             width = self.width - term_len(indent)
    104 | 
    105 |             if self.drop_whitespace and chunks[-1].strip() == "" and lines:
    106 |                 del chunks[-1]
    107 | 
    108 |             while chunks:
    109 |                 n = term_len(chunks[-1])
    110 | 
    111 |                 if cur_len + n <= width:
    112 |                     cur_line.append(chunks.pop())
    113 |                     cur_len += n
    114 | 
    115 |                 else:
    116 |                     break
    117 | 
    118 |             if chunks and term_len(chunks[-1]) > width:
    119 |                 self._handle_long_word(chunks, cur_line, cur_len, width)
    120 |                 cur_len = sum(map(term_len, cur_line))
    121 | 
    122 |             if self.drop_whitespace and cur_line and cur_line[-1].strip() == "":
    123 |                 cur_len -= term_len(cur_line[-1])
    124 |                 del cur_line[-1]
    125 | 
    126 |             if cur_line:
    127 |                 if (
    128 |                     self.max_lines is None
>>  129 |                     or len(lines) + 1 < self.max_lines
    130 |                     or (
    131 |                         not chunks
    132 |                         or self.drop_whitespace
    133 |                         and len(chunks) == 1
    134 |                         and not chunks[0].strip()
    135 |                     )
    136 |                     and cur_len <= width
    137 |                 ):
    138 |                     lines.append(indent + "".join(cur_line))
    139 |                 else:
    140 |                     while cur_line:
    141 |                         if (
    142 |                             cur_line[-1].strip()
    143 |                             and cur_len + term_len(self.placeholder) <= width
    144 |                         ):
    145 |                             cur_line.append(self.placeholder)
    146 |                             lines.append(indent + "".join(cur_line))
    147 |                             break
    148 |                         cur_len -= term_len(cur_line[-1])
    149 |                         del cur_line[-1]
    150 |                     else:
    151 |                         if lines:
    152 |                             prev_line = lines[-1].rstrip()
    153 |                             if (
    154 |                                 term_len(prev_line) + term_len(self.placeholder)
    155 |                                 <= self.width
    156 |                             ):
    157 |                                 lines[-1] = prev_line + self.placeholder
    158 |                                 break
    159 |                         lines.append(indent + self.placeholder.lstrip())
```

## M26  (src/itsdangerous/timed.py, operator: delete statement)
Mutation at line 127:  `last_exception = None  ->  pass`

```python
    118 |     def loads(self, s, max_age=None, return_timestamp=False, salt=None):
    119 |         """Reverse of :meth:`dumps`, raises :exc:`.BadSignature` if the
    120 |         signature validation fails. If a ``max_age`` is provided it will
    121 |         ensure the signature is not older than that time in seconds. In
    122 |         case the signature is outdated, :exc:`.SignatureExpired` is
    123 |         raised. All arguments are forwarded to the signer's
    124 |         :meth:`~TimestampSigner.unsign` method.
    125 |         """
    126 |         s = want_bytes(s)
>>  127 |         last_exception = None
    128 |         for signer in self.iter_unsigners(salt):
    129 |             try:
    130 |                 base64d, timestamp = signer.unsign(
    131 |                     s, max_age, return_timestamp=True
    132 |                 )
    133 |                 payload = self.load_payload(base64d)
    134 |                 if return_timestamp:
    135 |                     return payload, timestamp
    136 |                 return payload
    137 |             except BadSignature as err:
    138 |                 last_exception = err
    139 |         raise last_exception
```

## M27  (src/attr/_compat.py, operator: const 2->3)
Mutation at line 16:  `PY_3_11_PLUS = sys.version_info[:2] >= (3, 11)  ->  PY_3_11_PLUS = sys.version_info[:3] >= (3, 11)`

```python
      1 | # SPDX-License-Identifier: MIT
      2 | 
      3 | import inspect
      4 | import platform
      5 | import sys
      6 | import threading
      7 | 
      8 | from collections.abc import Mapping, Sequence  # noqa: F401
      9 | from typing import _GenericAlias
     10 | 
     11 | 
     12 | PYPY = platform.python_implementation() == "PyPy"
     13 | PY_3_8_PLUS = sys.version_info[:2] >= (3, 8)
     14 | PY_3_9_PLUS = sys.version_info[:2] >= (3, 9)
     15 | PY_3_10_PLUS = sys.version_info[:2] >= (3, 10)
>>   16 | PY_3_11_PLUS = sys.version_info[:2] >= (3, 11)
     17 | PY_3_12_PLUS = sys.version_info[:2] >= (3, 12)
     18 | PY_3_13_PLUS = sys.version_info[:2] >= (3, 13)
     19 | PY_3_14_PLUS = sys.version_info[:2] >= (3, 14)
     20 | 
     21 | 
     22 | if sys.version_info < (3, 8):
     23 |     try:
     24 |         from typing_extensions import Protocol
     25 |     except ImportError:  # pragma: no cover
     26 |         Protocol = object
     27 | else:
     28 |     from typing import Protocol  # noqa: F401
     29 | 
     30 | if PY_3_14_PLUS:  # pragma: no cover
     31 |     import annotationlib
```
