from __future__ import annotations

import os
import pty
import fcntl
import termios
import struct
from dataclasses import dataclass


@dataclass
class UnixPty:
    pid: int
    master_fd: int

    def set_nonblocking(self) -> None:
        flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def resize(self, cols: int, rows: int) -> None:
        winsz = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsz)

    def write(self, data: bytes) -> None:
        os.write(self.master_fd, data)

    def read(self, n: int = 4096) -> bytes:
        try:
            return os.read(self.master_fd, n)
        except BlockingIOError:
            return b""

    def terminate(self) -> None:
        try:
            os.kill(self.pid, 15)
        except Exception:
            pass


def spawn_unix(shell: str, cwd: str, cols: int, rows: int) -> UnixPty:
    pid, master_fd = pty.fork()
    if pid == 0:
        try:
            os.chdir(cwd)
        except Exception:
            os.chdir(os.path.expanduser("~"))
        os.execvp(shell, [shell])

    p = UnixPty(pid=pid, master_fd=master_fd)
    p.set_nonblocking()
    p.resize(cols=cols, rows=rows)
    return p