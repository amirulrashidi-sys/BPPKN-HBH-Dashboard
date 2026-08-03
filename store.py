"""Data layer for the BPPKN work-from-home roster.

One SQLite file holds two tables: `staff` (the directory) and `entry`
(one row per person per weekday per week). Anything not recorded in
`entry` is treated as a normal office day, so an empty database already
shows a full office.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

# ---------------------------------------------------------------- constants

TZ = ZoneInfo("Asia/Kuala_Lumpur")
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("WFH_DB_PATH", BASE_DIR / "wfh.db"))
SEED_CSV = BASE_DIR / "staff_seed.csv"

OFFICE = "PEJABAT"
WFH = "BDR"
LEAVE = "CUTI"
DUTY = "LUAR"

STATUSES = (OFFICE, WFH, LEAVE, DUTY)

STATUS_LABEL = {
    OFFICE: "Di pejabat",
    WFH: "Bekerja dari rumah",
    LEAVE: "Cuti",
    DUTY: "Tugas luar",
}
STATUS_SHORT = {OFFICE: "PEJABAT", WFH: "BDR", LEAVE: "CUTI", DUTY: "LUAR"}

# Policy: staff may claim up to two work-from-home days, Tuesday to Thursday.
WFH_WEEKDAYS = (2, 3, 4)          # ISO weekday numbers, Monday = 1
MAX_WFH_PER_WEEK = 2
WORK_WEEKDAYS = (1, 2, 3, 4, 5)   # Monday to Friday

DAY_FULL = {1: "Isnin", 2: "Selasa", 3: "Rabu", 4: "Khamis", 5: "Jumaat"}
DAY_ABBR = {1: "ISN", 2: "SEL", 3: "RAB", 4: "KHA", 5: "JUM"}
MONTH_BM = {
    1: "Januari", 2: "Februari", 3: "Mac", 4: "April", 5: "Mei", 6: "Jun",
    7: "Julai", 8: "Ogos", 9: "September", 10: "Oktober",
    11: "November", 12: "Disember",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS staff (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    position   TEXT    DEFAULT '',
    section    TEXT    DEFAULT '',
    sort_order INTEGER DEFAULT 999,
    active     INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS entry (
    staff_id   INTEGER NOT NULL,
    iso_year   INTEGER NOT NULL,
    iso_week   INTEGER NOT NULL,
    weekday    INTEGER NOT NULL,
    status     TEXT    NOT NULL,
    note       TEXT    DEFAULT '',
    updated_at TEXT    DEFAULT '',
    PRIMARY KEY (staff_id, iso_year, iso_week, weekday)
);
CREATE INDEX IF NOT EXISTS idx_entry_week ON entry (iso_year, iso_week);
"""


# ------------------------------------------------------------------ plumbing

@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=8000")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the tables, and seed the directory the first time only."""
    with connect() as conn:
        conn.executescript(SCHEMA)
        empty = conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0] == 0
    if empty and SEED_CSV.exists():
        seed = pd.read_csv(SEED_CSV)
        with connect() as conn:
            conn.executemany(
                "INSERT INTO staff (name, position, section, sort_order, active) "
                "VALUES (?, ?, ?, ?, 1)",
                seed[["name", "position", "section", "sort_order"]].itertuples(
                    index=False, name=None
                ),
            )


def now_stamp() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M")


def today() -> date:
    """Today in Malaysian time, regardless of where the server sits."""
    return datetime.now(TZ).date()


# ------------------------------------------------------------------ calendar

def current_week() -> tuple[int, int]:
    y, w, _ = today().isocalendar()
    return y, w


def week_dates(iso_year: int, iso_week: int) -> dict[int, date]:
    return {wd: date.fromisocalendar(iso_year, iso_week, wd) for wd in WORK_WEEKDAYS}


def shift_week(iso_year: int, iso_week: int, delta: int) -> tuple[int, int]:
    monday = date.fromisocalendar(iso_year, iso_week, 1)
    moved = monday.fromordinal(monday.toordinal() + delta * 7)
    y, w, _ = moved.isocalendar()
    return y, w


def week_range_label(iso_year: int, iso_week: int) -> str:
    days = week_dates(iso_year, iso_week)
    a, b = days[1], days[5]
    if a.month == b.month:
        return f"{a.day}\u2013{b.day} {MONTH_BM[b.month]} {b.year}"
    return f"{a.day} {MONTH_BM[a.month]} \u2013 {b.day} {MONTH_BM[b.month]} {b.year}"


def date_label(d: date) -> str:
    return f"{d.day} {MONTH_BM[d.month]} {d.year}"


# --------------------------------------------------------------------- staff

def list_staff(active_only: bool = True) -> pd.DataFrame:
    q = "SELECT id, name, position, section, sort_order, active FROM staff"
    if active_only:
        q += " WHERE active = 1"
    q += " ORDER BY sort_order, id"
    with connect() as conn:
        df = pd.read_sql_query(q, conn)
    return df


def section_order(staff: pd.DataFrame) -> list[str]:
    if staff.empty:
        return []
    ranked = staff.groupby("section", dropna=False)["sort_order"].min().sort_values()
    return [s if isinstance(s, str) and s.strip() else "Lain-lain" for s in ranked.index]


def save_staff(edited: pd.DataFrame) -> dict[str, int]:
    """Apply the directory table the admin edited: insert, update, delete."""
    edited = edited.copy()
    edited["name"] = edited["name"].fillna("").astype(str).str.strip()
    edited = edited[edited["name"] != ""]

    for col, default in (("position", ""), ("section", "Lain-lain")):
        edited[col] = edited[col].fillna(default).astype(str).str.strip()
        edited.loc[edited[col] == "", col] = default

    # Keep each section's members contiguous, ordered by where the section first
    # appears in the table, so a newly added officer lands beside their colleagues
    # instead of at the foot of the board.
    first_seen: dict[str, int] = {}
    for i, sec in enumerate(edited["section"]):
        first_seen.setdefault(sec, i)
    edited = (
        edited.assign(_rank=edited["section"].map(first_seen))
        .sort_values("_rank", kind="stable")
        .drop(columns="_rank")
        .reset_index(drop=True)
    )

    kept_ids, inserted, updated = [], 0, 0
    with connect() as conn:
        for order, row in enumerate(edited.to_dict("records"), start=1):
            sid = row.get("id")
            sid = None if sid is None or pd.isna(sid) else int(sid)
            vals = (row["name"], row["position"], row["section"], order)
            if sid is None:
                cur = conn.execute(
                    "INSERT INTO staff (name, position, section, sort_order, active) "
                    "VALUES (?, ?, ?, ?, 1)",
                    vals,
                )
                kept_ids.append(int(cur.lastrowid))
                inserted += 1
            else:
                conn.execute(
                    "UPDATE staff SET name=?, position=?, section=?, sort_order=?, "
                    "active=1 WHERE id=?",
                    vals + (sid,),
                )
                kept_ids.append(sid)
                updated += 1

        existing = [r[0] for r in conn.execute("SELECT id FROM staff").fetchall()]
        removed = [i for i in existing if i not in kept_ids]
        for sid in removed:
            conn.execute("DELETE FROM entry WHERE staff_id=?", (sid,))
            conn.execute("DELETE FROM staff WHERE id=?", (sid,))

    return {"inserted": inserted, "updated": updated, "removed": len(removed)}


# ------------------------------------------------------------------- entries

def week_entries(iso_year: int, iso_week: int) -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query(
            "SELECT staff_id, weekday, status, note, updated_at FROM entry "
            "WHERE iso_year=? AND iso_week=?",
            conn,
            params=(iso_year, iso_week),
        )


def status_matrix(iso_year: int, iso_week: int, staff: pd.DataFrame) -> pd.DataFrame:
    """Staff x weekday grid of statuses. Unrecorded days become PEJABAT."""
    grid = pd.DataFrame(OFFICE, index=staff["id"], columns=list(WORK_WEEKDAYS))
    notes = pd.DataFrame("", index=staff["id"], columns=list(WORK_WEEKDAYS))
    for row in week_entries(iso_year, iso_week).itertuples(index=False):
        if row.staff_id in grid.index and row.weekday in grid.columns:
            grid.at[row.staff_id, row.weekday] = row.status
            notes.at[row.staff_id, row.weekday] = row.note or ""
    grid.attrs["notes"] = notes
    return grid


def person_week(staff_id: int, iso_year: int, iso_week: int) -> dict[int, tuple[str, str]]:
    out = {wd: (OFFICE, "") for wd in WORK_WEEKDAYS}
    with connect() as conn:
        rows = conn.execute(
            "SELECT weekday, status, note FROM entry "
            "WHERE staff_id=? AND iso_year=? AND iso_week=?",
            (staff_id, iso_year, iso_week),
        ).fetchall()
    for r in rows:
        if r["weekday"] in out:
            out[r["weekday"]] = (r["status"], r["note"] or "")
    return out


def validate_week(plan: dict[int, str]) -> list[str]:
    """Return a list of policy problems; empty list means the plan is valid."""
    problems = []
    wfh_days = [wd for wd, s in plan.items() if s == WFH]
    if len(wfh_days) > MAX_WFH_PER_WEEK:
        problems.append(
            f"Anda memilih {len(wfh_days)} hari BDR. Maksimum {MAX_WFH_PER_WEEK} hari seminggu."
        )
    stray = sorted(wd for wd in wfh_days if wd not in WFH_WEEKDAYS)
    if stray:
        names = ", ".join(DAY_FULL[wd] for wd in stray)
        problems.append(f"BDR hanya dibenarkan Selasa hingga Khamis. Sila betulkan: {names}.")
    return problems


def save_person_week(
    staff_id: int,
    iso_year: int,
    iso_week: int,
    plan: dict[int, str],
    notes: dict[int, str] | None = None,
) -> None:
    notes = notes or {}
    stamp = now_stamp()
    with connect() as conn:
        for wd in WORK_WEEKDAYS:
            status = plan.get(wd, OFFICE)
            note = (notes.get(wd) or "").strip()
            if status == OFFICE and not note:
                conn.execute(
                    "DELETE FROM entry WHERE staff_id=? AND iso_year=? AND iso_week=? "
                    "AND weekday=?",
                    (staff_id, iso_year, iso_week, wd),
                )
            else:
                conn.execute(
                    "INSERT INTO entry (staff_id, iso_year, iso_week, weekday, status, "
                    "note, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(staff_id, iso_year, iso_week, weekday) DO UPDATE SET "
                    "status=excluded.status, note=excluded.note, "
                    "updated_at=excluded.updated_at",
                    (staff_id, iso_year, iso_week, wd, status, note, stamp),
                )


def clear_week(iso_year: int, iso_week: int) -> int:
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM entry WHERE iso_year=? AND iso_week=?", (iso_year, iso_week)
        )
        return cur.rowcount


def copy_week(src: tuple[int, int], dst: tuple[int, int]) -> int:
    stamp = now_stamp()
    with connect() as conn:
        rows = conn.execute(
            "SELECT staff_id, weekday, status, note FROM entry "
            "WHERE iso_year=? AND iso_week=?",
            src,
        ).fetchall()
        conn.execute("DELETE FROM entry WHERE iso_year=? AND iso_week=?", dst)
        conn.executemany(
            "INSERT INTO entry (staff_id, iso_year, iso_week, weekday, status, note, "
            "updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(r["staff_id"], dst[0], dst[1], r["weekday"], r["status"], r["note"], stamp)
             for r in rows],
        )
    return len(rows)


def last_updated(iso_year: int, iso_week: int) -> str | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT MAX(updated_at) FROM entry WHERE iso_year=? AND iso_week=?",
            (iso_year, iso_week),
        ).fetchone()
    return row[0] if row and row[0] else None


# ----------------------------------------------------------- backup, restore

def export_frames() -> dict[str, pd.DataFrame]:
    with connect() as conn:
        staff = pd.read_sql_query("SELECT * FROM staff ORDER BY sort_order, id", conn)
        entries = pd.read_sql_query(
            "SELECT * FROM entry ORDER BY iso_year, iso_week, staff_id, weekday", conn
        )
    return {"staff": staff, "entry": entries}


def import_frames(staff: pd.DataFrame, entries: pd.DataFrame) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM entry")
        conn.execute("DELETE FROM staff")
        staff.to_sql("staff", conn, if_exists="append", index=False)
        entries.to_sql("entry", conn, if_exists="append", index=False)
