from __future__ import annotations

from dataclasses import dataclass
import winpty  # type: ignore


@dataclass
class WindowsPty:
    pty: winpty.PtyProcess

    @property
    def pid(self) -> int | None:
        try:
            return int(self.pty.pid())
        except Exception:
            return None

    def resize(self, cols: int, rows: int) -> None:
        try:
            self.pty.set_size(cols, rows)
        except Exception:
            pass

    def write(self, data: bytes) -> None:
        text = data.decode("utf-8", errors="ignore")
        self.pty.write(text)

    def read(self, n: int = 4096) -> bytes:
        try:
            out = self.pty.read(n)
            return out.encode("utf-8", errors="ignore")
        except Exception:
            return b""

    def terminate(self) -> None:
        try:
            self.pty.close()
        except Exception:
            pass


def spawn_windows(shell: str, cwd: str, cols: int, rows: int) -> WindowsPty:
    p = winpty.PtyProcess.spawn(shell, cwd=cwd, dimensions=(rows, cols))
    return WindowsPty(pty=p)