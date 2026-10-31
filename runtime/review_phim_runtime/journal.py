"""Durable scope quota / process-state reservations. Requires an approved local DB root.

A failed or uncertain operation still consumes its reservation until a
separately authorized reconciliation. This is conservative by design.
"""
from dataclasses import dataclass
import sqlite3
from contextlib import contextmanager
from typing import Optional


@dataclass(frozen=True)
class JournalEntry:
    status: str
    pid: Optional[int] = None
    returncode: Optional[int] = None
    bytes_reserved: int = 0


class OperationJournal:
    def __init__(self, db_path: str):
        self.db_path = db_path
        with self._connect() as con:
            con.execute('''CREATE TABLE IF NOT EXISTS operations (
                scope_id TEXT NOT NULL,
                operation_key TEXT NOT NULL,
                bytes_reserved INTEGER NOT NULL,
                status TEXT NOT NULL,
                pid INTEGER,
                returncode INTEGER,
                PRIMARY KEY(scope_id, operation_key))''')

    @contextmanager
    def _connect(self):
        con = sqlite3.connect(self.db_path, timeout=30)
        try:
            con.execute('PRAGMA busy_timeout=30000')
            con.execute('PRAGMA synchronous=FULL')
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def reserve(self, scope_id: str, operation_key: str, amount: int, limit: int) -> JournalEntry:
        if not scope_id or not operation_key:
            return JournalEntry('BLOCKED_IDENTITY')
        if type(amount) is not int or type(limit) is not int or amount < 0 or limit <= 0 or amount > limit:
            return JournalEntry('BLOCKED_QUOTA')
        with self._connect() as con:
            con.execute('BEGIN IMMEDIATE')
            exists = con.execute('SELECT 1 FROM operations WHERE scope_id=? AND operation_key=?',
                                 (scope_id,operation_key)).fetchone()
            if exists:
                return JournalEntry('BLOCKED_DUPLICATE')
            used = con.execute('SELECT COALESCE(SUM(bytes_reserved),0) FROM operations WHERE scope_id=?',
                               (scope_id,)).fetchone()[0]
            if amount > limit - used:
                return JournalEntry('BLOCKED_QUOTA')
            con.execute('INSERT INTO operations(scope_id,operation_key,bytes_reserved,status) VALUES(?,?,?,?)',
                        (scope_id,operation_key,amount,'RESERVED'))
        return JournalEntry('RESERVED',bytes_reserved=amount)

    def mark_running(self, scope_id: str, operation_key: str, pid: int) -> bool:
        if type(pid) is not int or pid <= 0:
            return False
        with self._connect() as con:
            changed = con.execute('UPDATE operations SET status=?,pid=? WHERE scope_id=? AND operation_key=? AND status=?',
                                  ('RUNNING',pid,scope_id,operation_key,'RESERVED')).rowcount
        return changed == 1

    def mark_completed(self, scope_id: str, operation_key: str, returncode: int) -> bool:
        if type(returncode) is not int:
            return False
        with self._connect() as con:
            changed = con.execute('UPDATE operations SET status=?,returncode=? WHERE scope_id=? AND operation_key=? AND status=?',
                                  ('EXITED',returncode,scope_id,operation_key,'RUNNING')).rowcount
        return changed == 1

    def get(self, scope_id: str, operation_key: str) -> JournalEntry | None:
        with self._connect() as con:
            row = con.execute('SELECT status,pid,returncode,bytes_reserved FROM operations WHERE scope_id=? AND operation_key=?',
                              (scope_id,operation_key)).fetchone()
        return JournalEntry(*row) if row else None
