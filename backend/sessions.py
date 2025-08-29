from __future__ import annotations

import os
import sqlite3
import time
import uuid
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .namegen import generate_unique_name


DB_PATH = os.environ.get(
    "MULTI_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipelines", "multiplayer.sqlite3"),
)


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at REAL NOT NULL,
            status TEXT NOT NULL,
            min_budget INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS players (
            player_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        );

        CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY,
            payload TEXT
        );

        -- Ordered per-session pool provided by host
        CREATE TABLE IF NOT EXISTS session_samples (
            session_id TEXT NOT NULL,
            seq INTEGER NOT NULL,
            sample_id TEXT NOT NULL,
            dataset TEXT,
            table_name TEXT,
            row_index INTEGER,
            col_name TEXT,
            val TEXT,
            PRIMARY KEY(session_id, seq)
        );

        CREATE TABLE IF NOT EXISTS assignments (
            assignment_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            player_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            assigned_at REAL NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id),
            FOREIGN KEY(player_id) REFERENCES players(player_id),
            FOREIGN KEY(item_id) REFERENCES items(item_id)
        );

        CREATE TABLE IF NOT EXISTS labels (
            label_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            player_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            label_value TEXT,
            labeled_at REAL NOT NULL,
            UNIQUE(player_id, item_id),
            FOREIGN KEY(session_id) REFERENCES sessions(session_id),
            FOREIGN KEY(player_id) REFERENCES players(player_id),
            FOREIGN KEY(item_id) REFERENCES items(item_id)
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
        CREATE INDEX IF NOT EXISTS idx_players_session ON players(session_id);
        CREATE INDEX IF NOT EXISTS idx_assign_session_player ON assignments(session_id, player_id);
        CREATE INDEX IF NOT EXISTS idx_assign_session_item ON assignments(session_id, item_id);
        CREATE INDEX IF NOT EXISTS idx_labels_session_player ON labels(session_id, player_id);
        """
    )
    conn.commit()
    conn.close()


def _generate_session_id() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # avoid confusing chars
    return "".join(random.choices(alphabet, k=8))


def create_session(min_budget: int = 10) -> Dict:
    init_db()
    sid = _generate_session_id()
    created_at = time.time()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sessions(session_id, created_at, status, min_budget) VALUES (?,?,?,?)",
            (sid, created_at, "lobby", int(min_budget)),
        )
    return {"session_id": sid, "created_at": created_at, "status": "lobby", "min_budget": min_budget}


def get_session(session_id: str) -> Optional[sqlite3.Row]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        return row


def list_players(session_id: str) -> List[sqlite3.Row]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT player_id, display_name, role, status FROM players WHERE session_id=? ORDER BY rowid",
            (session_id,),
        ).fetchall()
        return rows


def create_player(session_id: str, role: str) -> Dict:
    sess = get_session(session_id)
    if not sess:
        raise ValueError("Session not found")
    used = {p["display_name"] for p in list_players(session_id)}
    display_name = generate_unique_name(used)
    player_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO players(player_id, session_id, display_name, role, status) VALUES (?,?,?,?,?)",
            (player_id, session_id, display_name, role, "lobby"),
        )
    return {"player_id": player_id, "display_name": display_name}


def seed_items_from_list(items: List[Tuple[str, str]]) -> int:
    """Seed items as (item_id, payload) list. Returns count inserted (ignores existing)."""
    init_db()
    with _connect() as conn:
        cur = conn.cursor()
        count = 0
        for iid, payload in items:
            try:
                cur.execute("INSERT OR IGNORE INTO items(item_id, payload) VALUES (?,?)", (str(iid), payload))
                count += cur.rowcount > 0
            except Exception:
                continue
        conn.commit()
    return int(count)


def seed_items_from_csv(csv_path: str, id_column: Optional[str] = None) -> int:
    import csv

    items: List[Tuple[str, str]] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        for i, row in enumerate(reader):
            item_id = row.get(id_column) if id_column else row.get("id") or str(i)
            payload = {k: row[k] for k in cols}
            items.append((str(item_id), str(payload)))
    return seed_items_from_list(items)


def _list_all_item_ids() -> List[str]:
    with _connect() as conn:
        rows = conn.execute("SELECT item_id FROM items").fetchall()
        return [r["item_id"] for r in rows]


def _assigned_items_in_session(session_id: str) -> set:
    with _connect() as conn:
        rows = conn.execute("SELECT item_id FROM assignments WHERE session_id=?", (session_id,)).fetchall()
        return {r["item_id"] for r in rows}


def start_session(session_id: str) -> Dict:
    sess = get_session(session_id)
    if not sess:
        raise ValueError("Session not found")
    if sess["status"] == "active":
        return {"status": "active"}

    min_budget = int(sess["min_budget"])
    players = list_players(session_id)
    if not players:
        raise ValueError("No players registered")

    # Use ordered session pool if provided by host
    with _connect() as conn:
        pool_rows = conn.execute(
            "SELECT seq, sample_id FROM session_samples WHERE session_id=? ORDER BY seq",
            (session_id,),
        ).fetchall()

    total_needed = min_budget * len(players)
    if not pool_rows or len(pool_rows) < total_needed:
        raise ValueError("Session pool not prepared by host or insufficient samples")

    assignments: List[Tuple[str, str, str, float]] = []  # (session_id, player_id, item_id, assigned_at)
    tnow = time.time()

    # Assign contiguous blocks per player
    for i, p in enumerate(players):
        pid = p["player_id"]
        start = i * min_budget
        end = start + min_budget
        for row in pool_rows[start:end]:
            sample_id = row["sample_id"]
            assignments.append((session_id, pid, sample_id, tnow))

    with _connect() as conn:
        cur = conn.cursor()
        cur.executemany(
            "INSERT OR REPLACE INTO assignments(assignment_id, session_id, player_id, item_id, assigned_at) VALUES (?,?,?,?,?)",
            [
                (str(uuid.uuid4()), session_id, pid, item_id, ts)
                for (session_id, pid, item_id, ts) in assignments
            ],
        )
        cur.execute("UPDATE sessions SET status='active' WHERE session_id=?", (session_id,))
        cur.execute(
            "UPDATE players SET status='labeling' WHERE session_id=? AND status='lobby'",
            (session_id,),
        )
        conn.commit()

    return {"status": "active", "assigned": len(assignments)}


def get_player_batch(session_id: str, player_id: str) -> List[Dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT a.item_id as sample_id,
                   s.dataset, s.table_name, s.row_index, s.col_name, s.val
            FROM assignments a
            JOIN session_samples s
              ON s.session_id = a.session_id AND s.sample_id = a.item_id
            WHERE a.session_id=? AND a.player_id=?
            ORDER BY a.assigned_at, s.seq
            """,
            (session_id, player_id),
        ).fetchall()
    return [
        {
            "sample_id": r["sample_id"],
            "dataset": r["dataset"],
            "table": r["table_name"],
            "row": r["row_index"],
            "col": r["col_name"],
            "val": r["val"],
        }
        for r in rows
    ]


def upsert_labels(session_id: str, player_id: str, labels: List[Dict[str, str]]) -> int:
    tnow = time.time()
    with _connect() as conn:
        cur = conn.cursor()
        count = 0
        for item in labels:
            iid = str(item.get("item_id") or item.get("sample_id"))
            val = str(item.get("label_value"))
            lid = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO labels(label_id, session_id, player_id, item_id, label_value, labeled_at)
                VALUES (?,?,?,?,?,?)
                ON CONFLICT(player_id, item_id) DO UPDATE SET
                    label_value=excluded.label_value,
                    labeled_at=excluded.labeled_at
                """,
                (lid, session_id, player_id, iid, val, tnow),
            )
            count += 1

        # If player finished all assigned items, mark done
        total_assigned = conn.execute(
            "SELECT COUNT(*) FROM assignments WHERE session_id=? AND player_id=?",
            (session_id, player_id),
        ).fetchone()[0]
        total_labeled = conn.execute(
            "SELECT COUNT(*) FROM labels WHERE session_id=? AND player_id=?",
            (session_id, player_id),
        ).fetchone()[0]
        if total_assigned > 0 and total_assigned == total_labeled:
            conn.execute("UPDATE players SET status='done' WHERE player_id=?", (player_id,))

        conn.commit()
    return count


def progress(session_id: str) -> Dict:
    sess = get_session(session_id)
    if not sess:
        raise ValueError("Session not found")
    players = list_players(session_id)
    players_out = [
        {"display_name": p["display_name"], "status": p["status"], "role": p["role"]}
        for p in players
    ]
    all_done = all(p["status"] == "done" for p in players if p["role"] != "host") and any(
        p["role"] == "host" for p in players
    )
    return {"players": players_out, "all_done": all_done, "status": sess["status"]}


def complete_session(session_id: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE sessions SET status='completed' WHERE session_id=?", (session_id,))
        conn.commit()


def save_session_pool(session_id: str, samples: List[Dict]) -> int:
    """Store ordered pool provided by host. Each item requires sample_id, dataset, table, row, col, val."""
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM session_samples WHERE session_id=?", (session_id,))
        seq = 0
        for s in samples:
            cur.execute(
                """
                INSERT INTO session_samples(session_id, seq, sample_id, dataset, table_name, row_index, col_name, val)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    session_id,
                    seq,
                    str(s.get("sample_id")),
                    str(s.get("dataset")),
                    str(s.get("table")),
                    int(s.get("row", 0)),
                    str(s.get("col")),
                    str(s.get("val")),
                ),
            )
            seq += 1
        conn.commit()
        return seq


def get_session_pool(session_id: str) -> List[Dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT seq, sample_id, dataset, table_name, row_index, col_name, val FROM session_samples WHERE session_id=? ORDER BY seq",
            (session_id,),
        ).fetchall()
    return [
        {
            "seq": r["seq"],
            "sample_id": r["sample_id"],
            "dataset": r["dataset"],
            "table": r["table_name"],
            "row": r["row_index"],
            "col": r["col_name"],
            "val": r["val"],
        }
        for r in rows
    ]


def merged_labels(session_id: str) -> List[Dict]:
    """Return merged labels across players keyed by sample_id. If multiple exist, latest wins."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT s.sample_id, s.dataset, s.table_name, s.row_index, s.col_name, s.val,
                   l.label_value, l.labeled_at
            FROM session_samples s
            LEFT JOIN labels l
              ON l.session_id = s.session_id AND l.item_id = s.sample_id
            WHERE s.session_id=?
            ORDER BY s.seq, l.labeled_at
            """,
            (session_id,),
        ).fetchall()
    # Reduce to latest label per sample
    merged: Dict[str, Dict] = {}
    for r in rows:
        sid = r["sample_id"]
        merged[sid] = {
            "sample_id": sid,
            "dataset": r["dataset"],
            "table": r["table_name"],
            "row": r["row_index"],
            "col": r["col_name"],
            "val": r["val"],
            "label_value": r["label_value"],
        }
    return list(merged.values())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Multiplayer Sessions DB utilities")
    sub = parser.add_subparsers(dest="cmd")

    seed = sub.add_parser("seed", help="Seed items from CSV or fake data")
    seed.add_argument("--csv", type=str, default=None, help="Path to CSV file")
    seed.add_argument("--id-column", type=str, default=None, help="Optional column for item_id")
    seed.add_argument("--fake", type=int, default=0, help="Seed N fake items if >0")

    args = parser.parse_args()
    init_db()

    if args.cmd == "seed":
        if args.csv:
            n = seed_items_from_csv(args.csv, args.id_column)
            print(f"Seeded {n} items from {args.csv}")
        elif args.fake and args.fake > 0:
            n = seed_items_from_list([(f"item-{i}", f"payload {i}") for i in range(args.fake)])
            print(f"Seeded {n} fake items")
        else:
            print("Nothing to seed; provide --csv or --fake N")
    else:
        parser.print_help()
