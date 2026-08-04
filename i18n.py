"""Bilingual labels for the roster board: Bahasa Melayu and English.

Everything the user reads lives here. `t(key, lang)` returns a string;
some entries are format templates used with `.format(...)`.
"""

from __future__ import annotations

from datetime import date

import store as S

LANGS = ("bm", "en")
LANG_NAME = {"bm": "Bahasa Melayu", "en": "English"}

DAY_FULL = {
    "bm": {1: "Isnin", 2: "Selasa", 3: "Rabu", 4: "Khamis", 5: "Jumaat"},
    "en": {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday"},
}
DAY_ABBR = {
    "bm": {1: "ISN", 2: "SEL", 3: "RAB", 4: "KHA", 5: "JUM"},
    "en": {1: "MON", 2: "TUE", 3: "WED", 4: "THU", 5: "FRI"},
}
MONTH = {
    "bm": {1: "Januari", 2: "Februari", 3: "Mac", 4: "April", 5: "Mei", 6: "Jun",
           7: "Julai", 8: "Ogos", 9: "September", 10: "Oktober",
           11: "November", 12: "Disember"},
    "en": {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
           7: "July", 8: "August", 9: "September", 10: "October",
           11: "November", 12: "December"},
}

# Short codes shown in the grid cells and the day cards.
STATUS_SHORT = {
    "bm": {S.OFFICE: "PEJABAT", S.WFH: "BDR", S.LEAVE: "CUTI", S.DUTY: "LUAR"},
    "en": {S.OFFICE: "OFFICE", S.WFH: "WFH", S.LEAVE: "LEAVE", S.DUTY: "DUTY"},
}
STATUS_LABEL = {
    "bm": {S.OFFICE: "Di pejabat", S.WFH: "Bekerja dari rumah",
           S.LEAVE: "Cuti", S.DUTY: "Tugas luar"},
    "en": {S.OFFICE: "In office", S.WFH: "Work from home",
           S.LEAVE: "On leave", S.DUTY: "Official duty"},
}

STRINGS: dict[str, dict[str, str]] = {
    # ---- masthead
    "app_title": {"bm": "Dashboard Jadual Bekerja Dari Rumah",
                  "en": "Work From Home Dashboard"},
    "org_line": {
        "bm": "Bahagian Perisikan dan Pengurusan Krisis Negara "
              "&middot; Majlis Keselamatan Negara &middot; Putrajaya",
        "en": "National Intelligence and Crisis Management Division "
              "&middot; National Security Council &middot; Putrajaya"},
    "week": {"bm": "Minggu", "en": "Week"},

    # ---- sidebar
    "sb_week": {"bm": "Minggu", "en": "Week"},
    "prev_week": {"bm": "◀ Sebelum", "en": "◀ Previous"},
    "next_week": {"bm": "Selepas ▶", "en": "Next ▶"},
    "this_week": {"bm": "Kembali ke minggu ini", "en": "Back to this week"},
    "sb_policy": {"bm": "Dasar", "en": "Policy"},
    "policy_text": {
        "bm": "Maksimum **{n} hari** bekerja dari rumah seminggu, "
              "**Selasa hingga Khamis** sahaja. Isnin dan Jumaat adalah hari "
              "wajib di pejabat.",
        "en": "Up to **{n} days** working from home per week, **Tuesday to "
              "Thursday** only. Monday and Friday are compulsory office days."},
    "sb_display": {"bm": "Paparan", "en": "Display"},
    "lang_label": {"bm": "Bahasa", "en": "Language"},
    "mode_label": {"bm": "Tema", "en": "Theme"},
    "mode_light": {"bm": "Terang", "en": "Light"},
    "mode_dark": {"bm": "Gelap", "en": "Dark"},
    "sb_admin": {"bm": "Pentadbir", "en": "Administrator"},
    "admin_code": {"bm": "Kod pentadbir", "en": "Admin code"},
    "admin_open": {"bm": "Buka akses", "en": "Unlock"},
    "admin_close": {"bm": "Tutup akses", "en": "Lock"},
    "admin_on": {"bm": "Akses pentadbir dibuka.", "en": "Admin access unlocked."},
    "admin_bad": {"bm": "Kod tidak sah.", "en": "Incorrect code."},
    "backup_dl": {"bm": "Muat turun sandaran", "en": "Download backup"},
    "backup_hint": {"bm": "Simpan sandaran ini setiap minggu.",
                    "en": "Save a backup every week."},

    # ---- day strip
    "in_office": {"bm": "di pejabat", "en": "in office"},
    "office_day": {"bm": "Hari wajib di pejabat", "en": "Compulsory office day"},
    "all_present": {"bm": "Semua hadir", "en": "All present"},
    "today_mark": {"bm": "Hari ini", "en": "Today"},

    # ---- tabs
    "tab_board": {"bm": "Papan Jadual", "en": "Roster Board"},
    "tab_mine": {"bm": "Jadual Saya", "en": "My Schedule"},
    "tab_summary": {"bm": "Ringkasan", "en": "Summary"},
    "tab_dir": {"bm": "Direktori", "en": "Directory"},

    # ---- board
    "col_name": {"bm": "Nama &amp; Jawatan", "en": "Name &amp; Position"},
    "sect_meta": {"bm": "{n} pegawai &middot; BDR {w} hari",
                  "en": "{n} officers &middot; WFH {w} days"},
    "today_note": {"bm": "Hari ini {day} {date}. Lajur hari ini ditanda kuning.",
                   "en": "Today is {day} {date}. Today's column is highlighted."},
    "other_week": {"bm": "Anda sedang melihat minggu lain. Hari ini {date}.",
                   "en": "You are viewing a different week. Today is {date}."},
    "last_update": {"bm": "Kemas kini terakhir: {stamp}", "en": "Last updated: {stamp}"},
    "no_records": {"bm": "belum ada rekod", "en": "no records yet"},
    "n_officers": {"bm": "{n} pegawai", "en": "{n} officers"},

    # ---- my schedule
    "pick_name": {"bm": "Pilih nama anda", "en": "Select your name"},
    "note_ph": {"bm": "Catatan", "en": "Note"},
    "quota_used": {"bm": "{used} daripada {max} hari BDR digunakan. Baki {left} hari.",
                   "en": "{used} of {max} WFH days used. {left} remaining."},
    "quota_full": {"bm": "Kedua-dua hari BDR telah digunakan.",
                   "en": "Both WFH days have been used."},
    "quota_over": {
        "bm": "Melebihi kuota: {used} hari BDR dipilih. Tukar {over} hari kembali "
              "kepada *Di pejabat* sebelum menyimpan.",
        "en": "Over quota: {used} WFH days selected. Set {over} back to *In office* "
              "before saving."},
    "save_mine": {"bm": "Simpan jadual saya", "en": "Save my schedule"},
    "saved_mine": {"bm": "Jadual {name} untuk minggu {week} disimpan.",
                   "en": "Schedule for {name}, week {week}, saved."},
    "dir_empty": {"bm": "Direktori masih kosong. Tambah nama di tab Direktori.",
                  "en": "The directory is empty. Add names in the Directory tab."},

    # ---- summary
    "by_section": {"bm": "Taburan mengikut seksyen", "en": "Breakdown by section"},
    "by_day": {"bm": "Taburan mengikut hari", "en": "Breakdown by day"},
    "coverage": {"bm": "Liputan pejabat", "en": "Office coverage"},
    "cover_ok": {
        "bm": "Setiap seksyen mempunyai sekurang-kurangnya seorang pegawai di "
              "pejabat pada setiap hari bekerja minggu ini.",
        "en": "Every section has at least one officer in the office on each "
              "working day this week."},
    "cover_flag": {"bm": "Tiada liputan", "en": "No coverage"},
    "cover_detail": {"bm": "{section} &mdash; {day}, {date}: tiada pegawai di pejabat.",
                     "en": "{section} &mdash; {day}, {date}: nobody in the office."},
    "unused_head": {"bm": "Pegawai belum penuh kuota BDR",
                    "en": "Officers with unused WFH quota"},
    "unused_none": {"bm": "Semua pegawai telah menggunakan kuota penuh.",
                    "en": "Every officer has used their full quota."},
    "th_name": {"bm": "Nama", "en": "Name"},
    "th_post": {"bm": "Jawatan", "en": "Position"},
    "th_section": {"bm": "Seksyen", "en": "Section"},
    "th_wfh_days": {"bm": "Hari BDR", "en": "WFH days"},
    "th_left": {"bm": "Baki", "en": "Remaining"},
    "dl_week": {"bm": "Muat turun jadual minggu ini",
                "en": "Download this week's roster"},

    # ---- directory
    "dir_locked": {"bm": "Masukkan kod pentadbir di bar sisi untuk menyunting direktori.",
                   "en": "Enter the admin code in the sidebar to edit the directory."},
    "dir_edit": {"bm": "Sunting direktori", "en": "Edit directory"},
    "dir_help": {
        "bm": "Tambah baris untuk pegawai baharu, sunting nama atau jawatan terus "
              "dalam jadual, dan buang baris untuk pegawai yang bertukar. Membuang "
              "seorang pegawai akan membuang rekod jadual beliau juga.",
        "en": "Add a row for a new officer, edit names or positions directly in the "
              "table, and delete a row when someone transfers out. Removing an "
              "officer also removes their schedule records."},
    "dir_save": {"bm": "Simpan direktori", "en": "Save directory"},
    "dir_saved": {"bm": "Direktori dikemas kini: {ins} baharu, {upd} disunting, {rem} dibuang.",
                  "en": "Directory updated: {ins} added, {upd} edited, {rem} removed."},
    "week_tools": {"bm": "Alat minggu", "en": "Week tools"},
    "copy_hint": {"bm": "Salin jadual minggu sebelum ke minggu ini.",
                  "en": "Copy last week's roster into this week."},
    "copy_btn": {"bm": "Salin dari minggu sebelum", "en": "Copy from last week"},
    "copied": {"bm": "{n} rekod disalin dari minggu {week}.",
               "en": "{n} records copied from week {week}."},
    "clear_hint": {"bm": "Kosongkan semua rekod bagi minggu yang sedang dipaparkan.",
                   "en": "Clear all records for the week on screen."},
    "clear_confirm": {"bm": "Saya pasti mahu kosongkan minggu {week}",
                      "en": "Yes, clear week {week}"},
    "clear_btn": {"bm": "Kosongkan minggu ini", "en": "Clear this week"},
    "cleared": {"bm": "{n} rekod dibuang.", "en": "{n} records removed."},
    "restore_head": {"bm": "Pulihkan dari sandaran", "en": "Restore from backup"},
    "restore_hint": {"bm": "Memuat naik sandaran akan menggantikan semua data semasa.",
                     "en": "Restoring a backup replaces all current data."},
    "restore_file": {"bm": "Fail sandaran .xlsx", "en": "Backup file (.xlsx)"},
    "restore_btn": {"bm": "Pulihkan sekarang", "en": "Restore now"},
    "restored": {"bm": "Data dipulihkan.", "en": "Data restored."},
    "restore_bad": {"bm": "Sandaran tidak dapat dibaca: {err}",
                    "en": "Could not read that backup: {err}"},

    # ---- validation (raised from store)
    "err_too_many": {"bm": "Anda memilih {n} hari BDR. Maksimum {max} hari seminggu.",
                     "en": "You selected {n} WFH days. The maximum is {max} per week."},
    "err_bad_day": {"bm": "BDR hanya dibenarkan Selasa hingga Khamis. Sila betulkan: {days}.",
                    "en": "WFH is only allowed Tuesday to Thursday. Please correct: {days}."},
}


def t(key: str, lang: str = "bm", **kw) -> str:
    """Look up a string and fill any {placeholders}."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("bm", key))
    return text.format(**kw) if kw else text


def week_range_label(iso_year: int, iso_week: int, lang: str = "bm") -> str:
    days = S.week_dates(iso_year, iso_week)
    a, b = days[1], days[5]
    m = MONTH[lang]
    if a.month == b.month:
        return f"{a.day}\u2013{b.day} {m[b.month]} {b.year}"
    return f"{a.day} {m[a.month]} \u2013 {b.day} {m[b.month]} {b.year}"


def date_label(d: date, lang: str = "bm") -> str:
    return f"{d.day} {MONTH[lang][d.month]} {d.year}"


def validation_messages(plan: dict[int, str], lang: str = "bm") -> list[str]:
    """Turn the policy problems found by store.validate_week into prose."""
    out = []
    wfh_days = [wd for wd, s in plan.items() if s == S.WFH]
    if len(wfh_days) > S.MAX_WFH_PER_WEEK:
        out.append(t("err_too_many", lang, n=len(wfh_days), max=S.MAX_WFH_PER_WEEK))
    stray = sorted(wd for wd in wfh_days if wd not in S.WFH_WEEKDAYS)
    if stray:
        names = ", ".join(DAY_FULL[lang][wd] for wd in stray)
        out.append(t("err_bad_day", lang, days=names))
    return out
