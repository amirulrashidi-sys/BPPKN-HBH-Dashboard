"""Look and feel for the roster board.

The visual model is an operations-room duty board: a printed roster form,
navy structural rules on cool paper, colour-coded status stamps, and a
single brass accent reserved for marking today. Every HTML builder here
returns one unbroken line so Streamlit's markdown renderer leaves it
alone.
"""

from __future__ import annotations

import html
from datetime import date

import pandas as pd

import store as S

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --paper:#EEF1F4; --panel:#FFFFFF; --ink:#12233F;
  --ink-70:rgba(18,35,63,.70); --ink-45:rgba(18,35,63,.45);
  --rule:rgba(18,35,63,.13); --rule-2:rgba(18,35,63,.28);
  --brass:#A8791C; --brass-soft:rgba(168,121,28,.10);
  --s-pejabat:#2E7D6B; --s-bdr:#2C6E9B; --s-cuti:#7A5AA0; --s-luar:#B25E28;
  --display:'Archivo',system-ui,sans-serif;
  --body:'IBM Plex Sans',system-ui,sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
}

.stApp { background:var(--paper); }
html, body, [class*="css"], .stMarkdown, .stMarkdown p { font-family:var(--body); color:var(--ink); }
.block-container { padding-top:3.6rem; padding-bottom:3rem; max-width:1400px; }
#MainMenu, footer, header [data-testid="stDecoration"] { visibility:hidden; }

/* ---------- masthead ---------- */
.mast { background:var(--ink); border-bottom:3px solid var(--brass); padding:17px 24px 16px;
        display:flex; justify-content:space-between; align-items:center; gap:20px; flex-wrap:wrap; }
.mast .mast-title { font-family:var(--display); font-weight:700; font-size:25px;
              letter-spacing:-.01em; color:#F4F2EC; line-height:1.2; margin:0; padding:0; }
.mast .mast-sub { font-family:var(--body); font-size:12px; color:rgba(244,242,236,.62);
            letter-spacing:.04em; margin:5px 0 0; padding:0; line-height:1.35; }
.mast-right { text-align:right; }
.mast .mast-week-line { display:flex; align-items:baseline; justify-content:flex-end; gap:9px; }
.mast .mast-week-eyebrow { font-family:var(--mono); font-size:10px; letter-spacing:.2em;
                     font-weight:500; color:#E3BB60; text-transform:uppercase; }
.mast .mast-week-no { font-family:var(--mono); font-weight:600; font-size:28px; color:#F4F2EC;
                line-height:1; font-variant-numeric:tabular-nums; }
.mast .mast-week-range { font-family:var(--body); font-size:12px; color:rgba(244,242,236,.72);
                margin:4px 0 0; line-height:1.3; }

/* ---------- day strip (the board's headline) ---------- */
.strip { display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin:16px 0 6px; }
.day { background:var(--panel); border:1px solid var(--rule); border-top:3px solid var(--rule-2);
       padding:11px 12px 12px; min-height:132px; position:relative; }
.day.today { border-top-color:var(--brass); box-shadow:0 1px 0 var(--rule), 0 6px 18px rgba(18,35,63,.07); }
.day.past { opacity:.62; }
.day .day-name { font-family:var(--display); font-weight:600; font-size:12.5px; letter-spacing:.09em;
            text-transform:uppercase; color:var(--ink-70); }
.day .day-date { font-family:var(--mono); font-size:10.5px; color:var(--ink-45); margin-top:1px; }
.day-mark { font-family:var(--mono); font-size:8.5px; letter-spacing:.15em; color:var(--brass);
            text-transform:uppercase; position:absolute; top:11px; right:12px; }
.day .day-count { font-family:var(--mono); font-weight:600; font-size:29px; line-height:1;
             margin-top:9px; font-variant-numeric:tabular-nums; color:var(--ink); }
.day .day-count small { font-family:var(--body); font-weight:400; font-size:10.5px;
                   letter-spacing:.05em; color:var(--ink-45); margin-left:4px; }
.day-away { margin-top:8px; border-top:1px solid var(--rule); padding-top:7px; }
.day .day-away-row { font-family:var(--body); font-size:11px; color:var(--ink-70);
                line-height:1.5; display:flex; gap:5px; align-items:baseline; }
.day-away-tag { font-family:var(--mono); font-size:8.5px; letter-spacing:.08em; flex:0 0 auto;
                padding:0 3px; border-radius:2px; }
.day-clear { font-size:10.5px; color:var(--ink-45); font-style:italic; margin-top:8px;
             border-top:1px solid var(--rule); padding-top:7px; }
.day-locked { font-size:10.5px; color:var(--ink-45); margin-top:8px;
              border-top:1px solid var(--rule); padding-top:7px; }

/* ---------- roster grid ---------- */
.board-wrap { overflow-x:auto; background:var(--panel); border:1px solid var(--rule); margin-top:4px; }
table.board { border-collapse:collapse; width:100%; min-width:900px; table-layout:fixed; }
table.board th, table.board td { border-bottom:1px solid var(--rule); padding:0;
                                 font-family:var(--body); color:var(--ink); }
.bh { background:#F7F8FA; position:sticky; top:0; z-index:3; border-bottom:1px solid var(--rule-2) !important; }
.bh div { font-family:var(--display); font-weight:600; font-size:10px; letter-spacing:.13em;
          text-transform:uppercase; color:var(--ink-70); padding:9px 10px; text-align:center; }
.bh.nm div { text-align:left; }
.bh.tdy div { color:var(--brass); }
.sect td { background:var(--ink); padding:6px 12px !important; }
.sect span { font-family:var(--mono); font-size:10px; letter-spacing:.14em; text-transform:uppercase;
             color:rgba(244,242,236,.86); }
.sect span i { color:var(--brass); font-style:normal; margin-left:8px; }
td.nm { position:sticky; left:0; background:var(--panel); z-index:2; border-right:1px solid var(--rule);
        min-width:330px; max-width:330px; }
td.nm div { padding:6px 12px; }
td.nm .nm-name { font-size:12.5px; font-weight:500; line-height:1.25; }
td.nm .nm-post { font-size:10px; color:var(--ink-45); margin-top:1px; }
td.cell { text-align:center; padding:4px 6px !important; }
td.cell.tdy { background:var(--brass-soft); }
.chip { display:inline-block; font-family:var(--mono); font-size:9px; font-weight:500;
        letter-spacing:.09em; padding:3px 7px; border-radius:2px; border:1px solid; white-space:nowrap; }
.chip-note { display:block; font-family:var(--body); font-size:9.5px; font-style:italic;
             color:var(--ink-45); margin-top:2px; letter-spacing:0; }
.c-PEJABAT { color:var(--s-pejabat); border-color:rgba(46,125,107,.32); background:rgba(46,125,107,.07); }
.c-BDR     { color:var(--s-bdr);     border-color:rgba(44,110,155,.36); background:rgba(44,110,155,.10); }
.c-CUTI    { color:var(--s-cuti);    border-color:rgba(122,90,160,.34); background:rgba(122,90,160,.09); }
.c-LUAR    { color:var(--s-luar);    border-color:rgba(178,94,40,.34);  background:rgba(178,94,40,.09); }
.chip.ghost { color:rgba(18,35,63,.22); border-color:transparent; background:transparent;
              font-size:13px; letter-spacing:0; padding:2px 7px; }

/* ---------- panels, legend, tally ---------- */
.panel { background:var(--panel); border:1px solid var(--rule); padding:14px 16px; margin-bottom:10px; }
.stMarkdown .panel-h, .panel-h { font-family:var(--display); font-weight:600; font-size:11px; letter-spacing:.14em;
           text-transform:uppercase; color:var(--ink-70); margin:0 0 10px; }
.legend { display:flex; gap:14px; flex-wrap:wrap; align-items:center; padding:9px 2px 2px; }
.legend-i { display:flex; gap:6px; align-items:center; font-size:11px; color:var(--ink-70); }
.legend-sw { width:12px; height:12px; border-radius:2px; border:1px solid; }
.tally-row { display:flex; align-items:center; gap:10px; margin-bottom:7px; }
.tally-row .tally-lab { flex:0 0 190px; font-size:11.5px; line-height:1.3; }
.tally-lab em { display:block; font-family:var(--mono); font-size:9px; font-style:normal;
                letter-spacing:.1em; color:var(--ink-45); text-transform:uppercase; }
.tally-bar { flex:1 1 auto; height:16px; background:rgba(18,35,63,.05); display:flex; }
.tally-seg { height:100%; }
.tally-row .tally-num { flex:0 0 58px; font-family:var(--mono); font-size:11px; text-align:right;
             color:var(--ink-70); font-variant-numeric:tabular-nums; }
.flag { border-left:3px solid var(--s-luar); background:rgba(178,94,40,.06); padding:8px 12px;
        font-size:11.5px; margin-bottom:6px; }
.flag b { font-family:var(--mono); font-size:10px; letter-spacing:.08em; color:var(--s-luar); }
.stamp { font-family:var(--mono); font-size:10px; letter-spacing:.05em; color:var(--ink-45);
         text-align:right; padding:10px 2px 0; }

/* ---------- streamlit widget tuning ---------- */
.stTabs [data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid var(--rule); }
.stTabs [data-baseweb="tab"] { font-family:var(--display); font-weight:600; font-size:11.5px;
                               letter-spacing:.09em; text-transform:uppercase; border-radius:0; }
.stButton button { border-radius:2px; font-family:var(--display); font-weight:600; font-size:11px;
                   letter-spacing:.08em; text-transform:uppercase; border:1px solid var(--rule-2);
                   color:var(--ink); background:var(--panel); }
.stButton button:hover { border-color:var(--brass); color:var(--brass); background:var(--panel); }
.stDownloadButton button { border-radius:2px; font-family:var(--display); font-weight:600;
                           font-size:11px; letter-spacing:.08em; text-transform:uppercase; }
[data-testid="stSidebar"] { background:var(--panel); border-right:1px solid var(--rule); }
[data-testid="stSidebar"] .stMarkdown h3 { font-family:var(--display); font-size:11px;
    letter-spacing:.14em; text-transform:uppercase; color:var(--ink-70); }

@media (max-width:820px) {
  .strip { grid-template-columns:repeat(2,1fr); }
  .mast { padding:14px 16px; }
  .mast-title { font-size:19px; }
}
@media (prefers-reduced-motion:reduce) { * { transition:none !important; animation:none !important; } }
</style>
"""

_SW = {
    S.OFFICE: ("var(--s-pejabat)", "rgba(46,125,107,.12)"),
    S.WFH: ("var(--s-bdr)", "rgba(44,110,155,.14)"),
    S.LEAVE: ("var(--s-cuti)", "rgba(122,90,160,.12)"),
    S.DUTY: ("var(--s-luar)", "rgba(178,94,40,.12)"),
}


def e(x) -> str:
    return html.escape(str(x if x is not None else ""))


RANKS = {"dsp", "asp", "supt", "mejar", "kapten", "leftenan", "lt", "kol", "kpl",
         "l/kpl", "sjn", "konst", "insp", "tuan", "dr"}
PARTICLES = {"bin", "binti", "bt", "b", "a/l", "a/p", "al", "ibni"}
# Words that rarely identify anyone on their own, so the next word is carried too.
GENERIC = {"mohd", "muhammad", "mohamad", "mohammad", "muhamad", "md", "nur", "noor",
           "nor", "siti", "wan", "ku", "abdul", "abd", "ab", "ahmad", "nik", "tengku",
           "syed", "sharifah", "che", "raja"}


def short_name(full: str, limit: int = 24) -> str:
    """Shorten a Malay name for a day card: rank, then the identifying word.

    "Noraffendy bin Abd Khalid" gives Noraffendy, but "Mohd Tarmizi bin Dan"
    keeps both words because Mohd alone identifies nobody.
    """
    parts = str(full).split()
    if not parts:
        return str(full)
    rank = ""
    if parts[0].lower().strip(".") in RANKS and len(parts) > 1:
        rank, parts = parts[0], parts[1:]
    core = [p for p in parts if p.lower().strip(".") not in PARTICLES]
    if not core:
        core = parts
    take = 2 if len(core) > 1 and core[0].lower().strip(".") in GENERIC else 1
    out = " ".join(([rank] if rank else []) + core[:take])
    return out if len(out) <= limit else out[: limit - 1].rstrip() + "\u2026"


# ------------------------------------------------------------------ masthead

def masthead(iso_year: int, iso_week: int) -> str:
    return "".join([
        '<div class="mast"><div>',
        '<div class="mast-title">Papan Jadual Bekerja Dari Rumah</div>',
        '<div class="mast-sub">Bahagian Perisikan dan Pengurusan Krisis Negara '
        '&middot; Majlis Keselamatan Negara &middot; Putrajaya</div>',
        '</div><div class="mast-right">',
        '<div class="mast-week-line"><span class="mast-week-eyebrow">Minggu</span>',
        f'<span class="mast-week-no">{iso_week:02d}</span></div>',
        f'<div class="mast-week-range">{e(S.week_range_label(iso_year, iso_week))}</div>',
        '</div></div>',
    ])


# ----------------------------------------------------------------- day strip

def day_strip(grid: pd.DataFrame, staff: pd.DataFrame, iso_year: int, iso_week: int) -> str:
    days = S.week_dates(iso_year, iso_week)
    td = S.today()
    names = dict(zip(staff["id"], staff["name"]))
    total = len(staff)
    parts = ['<div class="strip">']

    for wd in S.WORK_WEEKDAYS:
        d = days[wd]
        col = grid[wd] if wd in grid.columns else pd.Series(dtype=str)
        away = {S.WFH: [], S.LEAVE: [], S.DUTY: []}
        for sid, status in col.items():
            if status in away:
                away[status].append(names.get(sid, ""))
        in_office = total - sum(len(v) for v in away.values())

        cls = "day today" if d == td else ("day past" if d < td else "day")
        parts.append(f'<div class="{cls}">')
        if d == td:
            parts.append('<div class="day-mark">Hari ini</div>')
        parts.append(f'<div class="day-name">{S.DAY_FULL[wd]}</div>')
        parts.append(f'<div class="day-date">{d.day:02d}.{d.month:02d}.{d.year}</div>')
        parts.append(
            f'<div class="day-count">{in_office}'
            f'<small>/ {total} di pejabat</small></div>'
        )

        if wd not in S.WFH_WEEKDAYS and not any(away.values()):
            parts.append('<div class="day-locked">Hari wajib di pejabat</div>')
        elif not any(away.values()):
            parts.append('<div class="day-clear">Semua hadir</div>')
        else:
            parts.append('<div class="day-away">')
            for status in (S.WFH, S.LEAVE, S.DUTY):
                people = away[status]
                if not people:
                    continue
                fg, bg = _SW[status]
                shown = ", ".join(short_name(n) for n in people[:3])
                if len(people) > 3:
                    shown += f" +{len(people) - 3}"
                parts.append(
                    f'<div class="day-away-row">'
                    f'<span class="day-away-tag" style="color:{fg};background:{bg}">'
                    f'{S.STATUS_SHORT[status]}</span><span>{e(shown)}</span></div>'
                )
            parts.append('</div>')
        parts.append('</div>')

    parts.append('</div>')
    return "".join(parts)


# --------------------------------------------------------------- roster grid

def roster(grid: pd.DataFrame, staff: pd.DataFrame, iso_year: int, iso_week: int) -> str:
    days = S.week_dates(iso_year, iso_week)
    td = S.today()
    notes = grid.attrs.get("notes")
    parts = ['<div class="board-wrap"><table class="board">',
             '<colgroup><col style="width:330px">',
             '<col style="width:14%"><col style="width:14%"><col style="width:14%">',
             '<col style="width:14%"><col style="width:14%"></colgroup>',
             '<thead><tr><th class="bh nm"><div>Nama &amp; Jawatan</div></th>']
    for wd in S.WORK_WEEKDAYS:
        d = days[wd]
        tdy = " tdy" if d == td else ""
        parts.append(
            f'<th class="bh{tdy}"><div>{S.DAY_ABBR[wd]} {d.day:02d}/{d.month:02d}</div></th>'
        )
    parts.append('</tr></thead><tbody>')

    for section in S.section_order(staff):
        rows = staff[staff["section"] == section]
        if rows.empty:
            continue
        wfh_count = int((grid.loc[rows["id"]] == S.WFH).to_numpy().sum())
        parts.append(
            f'<tr class="sect"><td colspan="6"><span>{e(section)}'
            f'<i>{len(rows)} pegawai &middot; BDR {wfh_count} hari</i></span></td></tr>'
        )
        for r in rows.itertuples(index=False):
            parts.append('<tr>')
            parts.append(
                f'<td class="nm"><div><div class="nm-name">{e(r.name)}</div>'
                f'<div class="nm-post">{e(r.position)}</div></div></td>'
            )
            for wd in S.WORK_WEEKDAYS:
                status = grid.at[r.id, wd]
                note = notes.at[r.id, wd] if notes is not None else ""
                tdy = " tdy" if days[wd] == td else ""
                if status == S.OFFICE:
                    chip = '<span class="chip ghost" title="Di pejabat">&ndash;</span>'
                else:
                    chip = (f'<span class="chip c-{status}">'
                            f'{S.STATUS_SHORT[status]}</span>')
                if note:
                    chip += f'<span class="chip-note">{e(note)}</span>'
                parts.append(f'<td class="cell{tdy}">{chip}</td>')
            parts.append('</tr>')

    parts.append('</tbody></table></div>')
    return "".join(parts)


def legend() -> str:
    parts = ['<div class="legend">']
    for status in S.STATUSES:
        fg, bg = _SW[status]
        parts.append(
            f'<div class="legend-i"><span class="legend-sw" '
            f'style="border-color:{fg};background:{fg};opacity:.85"></span>'
            f'{S.STATUS_SHORT[status]} &mdash; {S.STATUS_LABEL[status]}</div>'
        )
    parts.append('</div>')
    return "".join(parts)


# --------------------------------------------------------------------- tally

def tally(grid: pd.DataFrame, staff: pd.DataFrame, by: str, iso_year: int, iso_week: int) -> str:
    """Stacked bars of status share, grouped either by section or by day."""
    parts = []
    if by == "section":
        groups = [(s, staff[staff["section"] == s]["id"].tolist(), f"{len(staff[staff['section'] == s])} pegawai")
                  for s in S.section_order(staff)]
    else:
        days = S.week_dates(iso_year, iso_week)
        groups = [(S.DAY_FULL[wd], None, f"{days[wd].day} {S.MONTH_BM[days[wd].month]}")
                  for wd in S.WORK_WEEKDAYS]

    for i, (label, ids, sub) in enumerate(groups):
        if by == "section":
            block = grid.loc[ids]
            counts = {s: int((block == s).to_numpy().sum()) for s in S.STATUSES}
        else:
            wd = S.WORK_WEEKDAYS[i]
            counts = {s: int((grid[wd] == s).sum()) for s in S.STATUSES}
        total = max(sum(counts.values()), 1)
        segs = "".join(
            f'<div class="tally-seg" style="width:{counts[s] / total * 100:.2f}%;'
            f'background:{_SW[s][0]}" title="{S.STATUS_SHORT[s]}: {counts[s]}"></div>'
            for s in S.STATUSES if counts[s]
        )
        parts.append(
            f'<div class="tally-row"><div class="tally-lab">{e(label)}<em>{e(sub)}</em></div>'
            f'<div class="tally-bar">{segs}</div>'
            f'<div class="tally-num">{counts[S.WFH]} BDR</div></div>'
        )
    return "".join(parts)


def coverage_flags(grid: pd.DataFrame, staff: pd.DataFrame, iso_year: int, iso_week: int) -> str:
    """Warn where a section has nobody in the office on a working day."""
    days = S.week_dates(iso_year, iso_week)
    out = []
    for section in S.section_order(staff):
        ids = staff[staff["section"] == section]["id"].tolist()
        for wd in S.WORK_WEEKDAYS:
            present = int((grid.loc[ids, wd] == S.OFFICE).sum())
            if present == 0 and ids:
                out.append(
                    f'<div class="flag"><b>Tiada liputan</b> &nbsp;{e(section)} '
                    f'&mdash; {S.DAY_FULL[wd]}, {days[wd].day} {S.MONTH_BM[days[wd].month]}: '
                    f'tiada pegawai di pejabat.</div>'
                )
    if not out:
        return ('<div class="panel" style="border-left:3px solid var(--s-pejabat)">'
                '<div style="font-size:11.5px">Setiap seksyen mempunyai sekurang-kurangnya '
                'seorang pegawai di pejabat pada setiap hari bekerja minggu ini.</div></div>')
    return "".join(out)
