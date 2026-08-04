"""Look and feel for the roster board, in light and dark.

The visual model is an operations-room duty board: a printed roster form,
structural rules on flat ground, colour-coded status stamps, and a single
brass accent reserved for marking today.

Two things this module is careful about. First, it declares colours for
Streamlit's own widgets rather than inheriting them, because the app can be
viewed under either of Streamlit's base themes and unstyled widgets end up
unreadable. Second, every HTML builder returns one unbroken line, so
Streamlit's markdown renderer leaves the markup alone.
"""

from __future__ import annotations

import html

import pandas as pd

import i18n as L
import store as S

MODES = ("light", "dark")

PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "paper": "#EEF1F4",
        "panel": "#FFFFFF",
        "ink": "#12233F",
        "ink-70": "rgba(18,35,63,.70)",
        "ink-45": "rgba(18,35,63,.45)",
        "ink-22": "rgba(18,35,63,.22)",
        "rule": "rgba(18,35,63,.13)",
        "rule-2": "rgba(18,35,63,.28)",
        "mast": "#12233F",
        "mast-fg": "#F4F2EC",
        "mast-fg-70": "rgba(244,242,236,.68)",
        "sect": "#12233F",
        "sect-fg": "rgba(244,242,236,.88)",
        "brass": "#A8791C",
        "brass-lit": "#E3BB60",
        "brass-soft": "rgba(168,121,28,.10)",
        "field": "#FFFFFF",
        "field-bd": "rgba(18,35,63,.22)",
        "shadow": "rgba(18,35,63,.07)",
        "on-brass": "#1A1408",
        "s-PEJABAT": "#2E7D6B", "s-PEJABAT-bg": "rgba(46,125,107,.07)",
        "s-PEJABAT-bd": "rgba(46,125,107,.32)",
        "s-BDR": "#2C6E9B", "s-BDR-bg": "rgba(44,110,155,.10)",
        "s-BDR-bd": "rgba(44,110,155,.36)",
        "s-CUTI": "#7A5AA0", "s-CUTI-bg": "rgba(122,90,160,.09)",
        "s-CUTI-bd": "rgba(122,90,160,.34)",
        "s-LUAR": "#B25E28", "s-LUAR-bg": "rgba(178,94,40,.09)",
        "s-LUAR-bd": "rgba(178,94,40,.34)",
    },
    "dark": {
        "paper": "#0B121B",
        "panel": "#151F2C",
        "ink": "#DCE3EB",
        "ink-70": "rgba(220,227,235,.70)",
        "ink-45": "rgba(220,227,235,.45)",
        "ink-22": "rgba(220,227,235,.22)",
        "rule": "rgba(220,227,235,.14)",
        "rule-2": "rgba(220,227,235,.28)",
        "mast": "#1B2A3D",
        "mast-fg": "#F1EFE8",
        "mast-fg-70": "rgba(241,239,232,.68)",
        "sect": "#22334A",
        "sect-fg": "rgba(241,239,232,.90)",
        "brass": "#D9A93F",
        "brass-lit": "#EFC96F",
        "brass-soft": "rgba(217,169,63,.13)",
        "field": "#0F1822",
        "field-bd": "rgba(220,227,235,.24)",
        "shadow": "rgba(0,0,0,.35)",
        "on-brass": "#12111A",
        "s-PEJABAT": "#5FB79E", "s-PEJABAT-bg": "rgba(95,183,158,.11)",
        "s-PEJABAT-bd": "rgba(95,183,158,.36)",
        "s-BDR": "#6BAEDD", "s-BDR-bg": "rgba(107,174,221,.14)",
        "s-BDR-bd": "rgba(107,174,221,.40)",
        "s-CUTI": "#B79BDD", "s-CUTI-bg": "rgba(183,155,221,.12)",
        "s-CUTI-bd": "rgba(183,155,221,.38)",
        "s-LUAR": "#E09A63", "s-LUAR-bg": "rgba(224,154,99,.12)",
        "s-LUAR-bd": "rgba(224,154,99,.38)",
    },
}

_STATIC_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

/* ---------- shell ---------- */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:var(--paper); }
[data-testid="stHeader"], [data-testid="stToolbar"] { background:var(--paper); }
html, body, .stMarkdown, .stMarkdown p { font-family:var(--body); color:var(--ink); }
.block-container { padding-top:3.6rem; padding-bottom:3rem; max-width:1400px; }
#MainMenu, footer, header [data-testid="stDecoration"] { visibility:hidden; }
hr, [data-testid="stDivider"] hr { border-color:var(--rule) !important; }

/* ---------- masthead ---------- */
.mast { background:var(--mast); border-bottom:3px solid var(--brass); padding:17px 24px 16px;
        display:flex; justify-content:space-between; align-items:center; gap:20px; flex-wrap:wrap; }
.mast .mast-title { font-family:var(--display); font-weight:700; font-size:25px;
        letter-spacing:-.01em; color:var(--mast-fg); line-height:1.2; margin:0; padding:0; }
.mast .mast-sub { font-family:var(--body); font-size:12px; color:var(--mast-fg-70);
        letter-spacing:.04em; margin:5px 0 0; padding:0; line-height:1.35; }
.mast-right { text-align:right; }
.mast .mast-week-line { display:flex; align-items:baseline; justify-content:flex-end; gap:9px; }
.mast .mast-week-eyebrow { font-family:var(--mono); font-size:10px; letter-spacing:.2em;
        font-weight:500; color:var(--brass-lit); text-transform:uppercase; }
.mast .mast-week-no { font-family:var(--mono); font-weight:600; font-size:28px;
        color:var(--mast-fg); line-height:1; font-variant-numeric:tabular-nums; }
.mast .mast-week-range { font-family:var(--body); font-size:12px; color:var(--mast-fg-70);
        margin:4px 0 0; line-height:1.3; }

/* ---------- day strip ---------- */
.strip { display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin:16px 0 6px; }
.day { background:var(--panel); border:1px solid var(--rule); border-top:3px solid var(--rule-2);
       padding:11px 12px 12px; min-height:132px; position:relative; }
.day.today { border-top-color:var(--brass); box-shadow:0 6px 18px var(--shadow); }
.day.past { opacity:.6; }
.day .day-name { font-family:var(--display); font-weight:600; font-size:12.5px;
       letter-spacing:.09em; text-transform:uppercase; color:var(--ink-70); }
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
       font-family:var(--body); color:var(--ink); background:transparent; }
.bh { background:var(--panel); position:sticky; top:0; z-index:3;
      border-bottom:1px solid var(--rule-2) !important; }
.bh div { font-family:var(--display); font-weight:600; font-size:10px; letter-spacing:.13em;
      text-transform:uppercase; color:var(--ink-70); padding:9px 10px; text-align:center; }
.bh.nm div { text-align:left; }
.bh.tdy div { color:var(--brass); }
tr.sect td { background:var(--sect); padding:6px 12px !important; }
tr.sect span { font-family:var(--mono); font-size:10px; letter-spacing:.14em;
      text-transform:uppercase; color:var(--sect-fg); }
tr.sect span i { color:var(--brass-lit); font-style:normal; margin-left:8px; }
td.nm { position:sticky; left:0; background:var(--panel) !important; z-index:2;
      border-right:1px solid var(--rule); min-width:330px; max-width:330px; }
td.nm div { padding:6px 12px; }
td.nm .nm-name { font-family:var(--body); font-size:12.5px; font-weight:500; line-height:1.25; }
td.nm .nm-post { font-family:var(--body); font-size:10px; color:var(--ink-45); margin-top:1px; }
td.cell { text-align:center; padding:4px 6px !important; }
td.cell.tdy { background:var(--brass-soft) !important; }
.chip { display:inline-block; font-family:var(--mono); font-size:9px; font-weight:500;
      letter-spacing:.09em; padding:3px 7px; border-radius:2px; border:1px solid; white-space:nowrap; }
.chip-note { display:block; font-family:var(--body); font-size:9.5px; font-style:italic;
      color:var(--ink-45); margin-top:2px; letter-spacing:0; }
.c-PEJABAT { color:var(--s-PEJABAT); border-color:var(--s-PEJABAT-bd); background:var(--s-PEJABAT-bg); }
.c-BDR     { color:var(--s-BDR);     border-color:var(--s-BDR-bd);     background:var(--s-BDR-bg); }
.c-CUTI    { color:var(--s-CUTI);    border-color:var(--s-CUTI-bd);    background:var(--s-CUTI-bg); }
.c-LUAR    { color:var(--s-LUAR);    border-color:var(--s-LUAR-bd);    background:var(--s-LUAR-bg); }
.chip.ghost { color:var(--ink-22); border-color:transparent; background:transparent;
      font-size:13px; letter-spacing:0; padding:2px 7px; }

/* ---------- panels, legend, tally ---------- */
.panel { background:var(--panel); border:1px solid var(--rule); padding:14px 16px; margin-bottom:10px; }
.stMarkdown .panel-h, .panel-h { font-family:var(--display); font-weight:600; font-size:11px;
      letter-spacing:.14em; text-transform:uppercase; color:var(--ink-70); margin:0 0 10px; }
.legend { display:flex; gap:14px; flex-wrap:wrap; align-items:center; padding:9px 2px 2px; }
.legend-i { display:flex; gap:6px; align-items:center; font-size:11px; color:var(--ink-70); }
.legend-sw { width:12px; height:12px; border-radius:2px; border:1px solid; }
.tally-row { display:flex; align-items:center; gap:10px; margin-bottom:7px; }
.tally-row .tally-lab { flex:0 0 190px; font-size:11.5px; line-height:1.3; color:var(--ink); }
.tally-lab em { display:block; font-family:var(--mono); font-size:9px; font-style:normal;
      letter-spacing:.1em; color:var(--ink-45); text-transform:uppercase; }
.tally-bar { flex:1 1 auto; height:16px; background:var(--rule); display:flex; }
.tally-seg { height:100%; }
.tally-row .tally-num { flex:0 0 74px; font-family:var(--mono); font-size:11px; text-align:right;
      color:var(--ink-70); font-variant-numeric:tabular-nums; }
.flag { border-left:3px solid var(--s-LUAR); background:var(--s-LUAR-bg); padding:8px 12px;
      font-size:11.5px; margin-bottom:6px; color:var(--ink); }
.flag b { font-family:var(--mono); font-size:10px; letter-spacing:.08em; color:var(--s-LUAR); }
.stamp { font-family:var(--mono); font-size:10px; letter-spacing:.05em; color:var(--ink-45);
      text-align:right; padding:10px 2px 0; }

/* themed read-only table, used instead of st.dataframe */
table.flat { border-collapse:collapse; width:100%; background:var(--panel);
      border:1px solid var(--rule); }
table.flat th { font-family:var(--display); font-size:10px; letter-spacing:.12em;
      text-transform:uppercase; color:var(--ink-70); text-align:left; padding:8px 12px;
      border-bottom:1px solid var(--rule-2); background:var(--panel); }
table.flat td { font-family:var(--body); font-size:12px; color:var(--ink); padding:7px 12px;
      border-bottom:1px solid var(--rule); background:transparent; }
table.flat td.num { font-family:var(--mono); text-align:right; font-variant-numeric:tabular-nums; }

/* ---------- Streamlit widgets: declared, not inherited ---------- */
[data-testid="stSidebar"] { background:var(--panel); border-right:1px solid var(--rule); }
[data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] label p { color:var(--ink); }
[data-testid="stSidebar"] .stMarkdown h3 { font-family:var(--display); font-size:11px;
      letter-spacing:.14em; text-transform:uppercase; color:var(--ink-70); }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
.stRadio label p, .stCheckbox label p, label[data-baseweb="radio"] div,
label[data-baseweb="checkbox"] span { color:var(--ink) !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color:var(--ink-70) !important; }
[data-testid="stRadio"], [data-testid="stRadioGroup"], [data-testid="stRadioOption"],
[data-testid="stCheckbox"], [data-testid="stTab"], [data-testid="stTextInput"],
[data-testid="stSelectbox"], [data-testid="stButton"], [data-testid="stDownloadButton"],
[data-testid="stFileUploader"], [data-testid="stAlert"] { color:var(--ink) !important; }
[data-testid="stRadioOption"] span, [data-testid="stCheckbox"] span { color:var(--ink) !important; }

.stTextInput input, .stTextArea textarea, .stNumberInput input {
      background:var(--field) !important; color:var(--ink) !important;
      border:1px solid var(--field-bd) !important; border-radius:2px !important; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color:var(--ink-45) !important; }
[data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"],
.stTextInput [data-baseweb="input"], .stTextInput [data-baseweb="base-input"],
.stTextArea [data-baseweb="textarea"] { background:var(--field) !important;
      border:1px solid var(--field-bd) !important; border-radius:2px !important; }
[data-testid="stTextInputRootElement"] input { border:0 !important; }
.stTextInput button svg, .stTextInput svg { fill:var(--ink-70) !important; }

/* Streamlit 1.60 builds selectboxes with react-aria; older builds use baseweb,
   so both are covered here. */
.react-aria-ComboBox > div, [data-baseweb="select"] > div {
      background:var(--field) !important; border:1px solid var(--field-bd) !important;
      border-radius:2px !important; }
.react-aria-ComboBox, .react-aria-ComboBox div, .react-aria-ComboBox span,
.react-aria-ComboBox input, [data-baseweb="select"] div, [data-baseweb="select"] span,
[data-baseweb="select"] input { color:var(--ink) !important; }
.react-aria-ComboBox input::placeholder { color:var(--ink-45) !important; }
.react-aria-ComboBox svg, [data-baseweb="select"] svg { fill:var(--ink-70) !important; }
.react-aria-Popover, .react-aria-ListBox, [data-baseweb="popover"] div,
[data-baseweb="popover"] ul, [data-baseweb="menu"] { background:var(--panel) !important;
      border:1px solid var(--rule) !important; }
.react-aria-Option, .react-aria-ListBox div, .react-aria-ListBox span,
[data-baseweb="popover"] li, [data-baseweb="menu"] li { color:var(--ink) !important; }
.react-aria-Option[data-focused], .react-aria-Option[data-selected],
.react-aria-Option:hover, [data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover {
      background:var(--brass-soft) !important; }

[data-baseweb="radio"] div[aria-checked="false"] { background:var(--field) !important;
      border-color:var(--field-bd) !important; }
[data-baseweb="radio"] div[aria-checked="true"] { background:var(--brass) !important;
      border-color:var(--brass) !important; }

/* Streamlit 1.60 marks tabs with data-testid, not data-baseweb */
.stTabs [role="tablist"] { gap:26px; border-bottom:1px solid var(--rule); background:transparent; }
[data-testid="stTab"] { border-radius:0; background:transparent; }
[data-testid="stTab"] p { font-family:var(--display); font-weight:600; font-size:11.5px;
      letter-spacing:.09em; text-transform:uppercase; color:var(--ink-45) !important; }
[data-testid="stTab"]:hover p { color:var(--ink-70) !important; }
[data-testid="stTab"][aria-selected="true"] p { color:var(--ink) !important; }
[data-baseweb="tab-highlight"], [data-testid="stTabHighlight"] { background:var(--brass) !important; }

.stButton button, .stDownloadButton button, .stFormSubmitButton button {
      border-radius:2px; font-family:var(--display); font-weight:600; font-size:11px;
      letter-spacing:.08em; text-transform:uppercase;
      border:1px solid var(--rule-2) !important; color:var(--ink) !important;
      background:var(--panel) !important; }
.stButton button p, .stDownloadButton button p { color:var(--ink) !important; }
.stButton button:hover, .stDownloadButton button:hover {
      border-color:var(--brass) !important; background:var(--brass-soft) !important; }
.stButton button:hover p { color:var(--brass) !important; }
.stButton button[kind="primary"] { background:var(--brass) !important;
      border-color:var(--brass) !important; }
.stButton button[kind="primary"] p { color:var(--on-brass) !important; }
.stButton button:disabled, .stButton button:disabled p { color:var(--ink-45) !important; }

[data-testid="stFileUploaderDropzone"] { background:var(--field) !important;
      border:1px dashed var(--field-bd) !important; }
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] div { color:var(--ink-70) !important; }
[data-testid="stExpander"] { background:var(--panel); border:1px solid var(--rule); }

@media (max-width:820px) {
  .strip { grid-template-columns:repeat(2,1fr); }
  .mast { padding:14px 16px; }
  .mast .mast-title { font-size:19px; }
}
@media (prefers-reduced-motion:reduce) { * { transition:none !important; animation:none !important; } }
"""


def css(mode: str = "light") -> str:
    """Build the stylesheet for one palette."""
    pal = PALETTES.get(mode, PALETTES["light"])
    tokens = "".join(f"--{k}:{v};" for k, v in pal.items())
    tokens += ("--display:'Archivo',system-ui,sans-serif;"
               "--body:'IBM Plex Sans',system-ui,sans-serif;"
               "--mono:'IBM Plex Mono',ui-monospace,monospace;")
    return f"<style>{_STATIC_CSS}\n:root{{{tokens}}}</style>"


def _sw(mode: str, status: str) -> tuple[str, str]:
    pal = PALETTES.get(mode, PALETTES["light"])
    return pal[f"s-{status}"], pal[f"s-{status}-bg"]


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

def masthead(iso_year: int, iso_week: int, lang: str) -> str:
    return "".join([
        '<div class="mast"><div>',
        f'<div class="mast-title">{L.t("app_title", lang)}</div>',
        f'<div class="mast-sub">{L.t("org_line", lang)}</div>',
        '</div><div class="mast-right">',
        f'<div class="mast-week-line"><span class="mast-week-eyebrow">'
        f'{L.t("week", lang)}</span>',
        f'<span class="mast-week-no">{iso_week:02d}</span></div>',
        f'<div class="mast-week-range">'
        f'{e(L.week_range_label(iso_year, iso_week, lang))}</div>',
        '</div></div>',
    ])


# ----------------------------------------------------------------- day strip

def day_strip(grid: pd.DataFrame, staff: pd.DataFrame, iso_year: int, iso_week: int,
              lang: str, mode: str) -> str:
    days = S.week_dates(iso_year, iso_week)
    td = S.today()
    names = dict(zip(staff["id"], staff["name"]))
    short = L.STATUS_SHORT[lang]
    total = len(staff)
    parts = ['<div class="strip">']

    for wd in S.WORK_WEEKDAYS:
        d = days[wd]
        col = grid[wd] if wd in grid.columns else pd.Series(dtype=str)
        away: dict[str, list[str]] = {S.WFH: [], S.LEAVE: [], S.DUTY: []}
        for sid, status in col.items():
            if status in away:
                away[status].append(names.get(sid, ""))
        in_office = total - sum(len(v) for v in away.values())

        cls = "day today" if d == td else ("day past" if d < td else "day")
        parts.append(f'<div class="{cls}">')
        if d == td:
            parts.append(f'<div class="day-mark">{L.t("today_mark", lang)}</div>')
        parts.append(f'<div class="day-name">{L.DAY_FULL[lang][wd]}</div>')
        parts.append(f'<div class="day-date">{d.day:02d}.{d.month:02d}.{d.year}</div>')
        parts.append(f'<div class="day-count">{in_office}'
                     f'<small>/ {total} {L.t("in_office", lang)}</small></div>')

        if wd not in S.WFH_WEEKDAYS and not any(away.values()):
            parts.append(f'<div class="day-locked">{L.t("office_day", lang)}</div>')
        elif not any(away.values()):
            parts.append(f'<div class="day-clear">{L.t("all_present", lang)}</div>')
        else:
            parts.append('<div class="day-away">')
            for status in (S.WFH, S.LEAVE, S.DUTY):
                people = away[status]
                if not people:
                    continue
                fg, bg = _sw(mode, status)
                shown = ", ".join(short_name(n) for n in people[:3])
                if len(people) > 3:
                    shown += f" +{len(people) - 3}"
                parts.append(
                    f'<div class="day-away-row">'
                    f'<span class="day-away-tag" style="color:{fg};background:{bg}">'
                    f'{short[status]}</span><span>{e(shown)}</span></div>'
                )
            parts.append('</div>')
        parts.append('</div>')

    parts.append('</div>')
    return "".join(parts)


# --------------------------------------------------------------- roster grid

def roster(grid: pd.DataFrame, staff: pd.DataFrame, iso_year: int, iso_week: int,
           lang: str) -> str:
    days = S.week_dates(iso_year, iso_week)
    td = S.today()
    notes = grid.attrs.get("notes")
    short = L.STATUS_SHORT[lang]
    parts = ['<div class="board-wrap"><table class="board">',
             '<colgroup><col style="width:330px">',
             '<col style="width:14%"><col style="width:14%"><col style="width:14%">',
             '<col style="width:14%"><col style="width:14%"></colgroup>',
             f'<thead><tr><th class="bh nm"><div>{L.t("col_name", lang)}</div></th>']
    for wd in S.WORK_WEEKDAYS:
        d = days[wd]
        tdy = " tdy" if d == td else ""
        parts.append(f'<th class="bh{tdy}"><div>{L.DAY_ABBR[lang][wd]} '
                     f'{d.day:02d}/{d.month:02d}</div></th>')
    parts.append('</tr></thead><tbody>')

    for section in S.section_order(staff):
        rows = staff[staff["section"] == section]
        if rows.empty:
            continue
        wfh_count = int((grid.loc[rows["id"]] == S.WFH).to_numpy().sum())
        meta = L.t("sect_meta", lang, n=len(rows), w=wfh_count)
        parts.append(f'<tr class="sect"><td colspan="6"><span>{e(section)}'
                     f'<i>{meta}</i></span></td></tr>')
        for r in rows.itertuples(index=False):
            parts.append('<tr>')
            parts.append(f'<td class="nm"><div><div class="nm-name">{e(r.name)}</div>'
                         f'<div class="nm-post">{e(r.position)}</div></div></td>')
            for wd in S.WORK_WEEKDAYS:
                status = grid.at[r.id, wd]
                note = notes.at[r.id, wd] if notes is not None else ""
                tdy = " tdy" if days[wd] == td else ""
                if status == S.OFFICE:
                    chip = ('<span class="chip ghost" title='
                            f'"{L.STATUS_LABEL[lang][S.OFFICE]}">&ndash;</span>')
                else:
                    chip = f'<span class="chip c-{status}">{short[status]}</span>'
                if note:
                    chip += f'<span class="chip-note">{e(note)}</span>'
                parts.append(f'<td class="cell{tdy}">{chip}</td>')
            parts.append('</tr>')

    parts.append('</tbody></table></div>')
    return "".join(parts)


def legend(lang: str, mode: str) -> str:
    parts = ['<div class="legend">']
    for status in S.STATUSES:
        fg, _ = _sw(mode, status)
        parts.append(
            f'<div class="legend-i"><span class="legend-sw" '
            f'style="border-color:{fg};background:{fg};opacity:.85"></span>'
            f'{L.STATUS_SHORT[lang][status]} &mdash; {L.STATUS_LABEL[lang][status]}</div>'
        )
    parts.append('</div>')
    return "".join(parts)


# --------------------------------------------------------------------- tally

def tally(grid: pd.DataFrame, staff: pd.DataFrame, by: str, iso_year: int,
          iso_week: int, lang: str, mode: str) -> str:
    """Stacked bars of status share, grouped either by section or by day."""
    parts = []
    wfh_short = L.STATUS_SHORT[lang][S.WFH]
    if by == "section":
        groups = [(s, staff[staff["section"] == s]["id"].tolist(),
                   L.t("n_officers", lang, n=len(staff[staff["section"] == s])))
                  for s in S.section_order(staff)]
    else:
        days = S.week_dates(iso_year, iso_week)
        groups = [(L.DAY_FULL[lang][wd], None,
                   f"{days[wd].day} {L.MONTH[lang][days[wd].month]}")
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
            f'background:{_sw(mode, s)[0]}" '
            f'title="{L.STATUS_SHORT[lang][s]}: {counts[s]}"></div>'
            for s in S.STATUSES if counts[s]
        )
        parts.append(
            f'<div class="tally-row"><div class="tally-lab">{e(label)}<em>{e(sub)}</em></div>'
            f'<div class="tally-bar">{segs}</div>'
            f'<div class="tally-num">{counts[S.WFH]} {wfh_short}</div></div>'
        )
    return "".join(parts)


def coverage_flags(grid: pd.DataFrame, staff: pd.DataFrame, iso_year: int,
                   iso_week: int, lang: str) -> str:
    """Warn where a section has nobody in the office on a working day."""
    days = S.week_dates(iso_year, iso_week)
    out = []
    for section in S.section_order(staff):
        ids = staff[staff["section"] == section]["id"].tolist()
        for wd in S.WORK_WEEKDAYS:
            if ids and int((grid.loc[ids, wd] == S.OFFICE).sum()) == 0:
                detail = L.t("cover_detail", lang, section=e(section),
                             day=L.DAY_FULL[lang][wd],
                             date=f"{days[wd].day} {L.MONTH[lang][days[wd].month]}")
                out.append(f'<div class="flag"><b>{L.t("cover_flag", lang)}</b> '
                           f'&nbsp;{detail}</div>')
    if not out:
        return ('<div class="panel" style="border-left:3px solid var(--s-PEJABAT)">'
                f'<div style="font-size:11.5px">{L.t("cover_ok", lang)}</div></div>')
    return "".join(out)


# --------------------------------------------------------------- flat tables

def flat_table(headers: list[str], rows: list[list],
               numeric: set[int] | None = None) -> str:
    """A themed read-only table, used instead of st.dataframe.

    st.dataframe draws into a canvas that follows Streamlit's own base theme,
    so it cannot follow the light/dark switch in this app.
    """
    numeric = numeric or set()
    parts = ['<div class="board-wrap"><table class="flat"><thead><tr>']
    parts += [f'<th>{e(h)}</th>' for h in headers]
    parts.append('</tr></thead><tbody>')
    for row in rows:
        parts.append('<tr>')
        for i, cell in enumerate(row):
            cls = ' class="num"' if i in numeric else ''
            parts.append(f'<td{cls}>{e(cell)}</td>')
        parts.append('</tr>')
    parts.append('</tbody></table></div>')
    return "".join(parts)
