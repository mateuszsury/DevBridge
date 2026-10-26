import tempfile
from pathlib import Path
import unittest
from webterm.db import DB
from webterm.terminal_manager import TerminalManager

class RestartTests(unittest.IsolatedAsyncioTestCase):
    async def test_restart_keeps_history_without_claiming_a_live_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            db = DB(str(Path(directory) / 'sessions.sqlite3'))
            db.upsert_session(session_id='before-restart', cwd=directory,
                shell='/bin/sh', pid=123, status='running', created_at=1,
                last_activity_at=2, cols=80, rows=24, scrollback='saved output')
            manager = TerminalManager(db)
            await manager.mark_db_sessions_stale_on_start()
            await manager.load_sessions_from_db()
            restored = manager.sessions['before-restart']
            self.assertEqual(restored.status, 'stale')
            self.assertEqual(restored.scrollback, 'saved output')
            self.assertIsNone(restored.pty)
            self.assertEqual(await manager.list_sessions(), [])

if __name__ == '__main__': unittest.main()
