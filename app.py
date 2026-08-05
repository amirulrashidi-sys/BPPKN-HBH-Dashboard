"""Dashboard Hari Bekerja Hibrid — BPPKN, Majlis Keselamatan Negara.

Run locally:      streamlit run app.py
Share on the LAN: streamlit run app.py --server.address 0.0.0.0 --server.port 8501

Language and theme are held in the URL (?lang=en&mode=dark) so a person's
choice survives a page reload and can be sent to someone else as a link.
"""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

import i18n as L
import store as S
import theme as T

st.set_page_config(
    page_title="Papan Jadual BDR · BPPKN",
    page_icon="🗓",
    layout="wide",
    initial_sidebar_state="expanded",
)

S.init_db()


def _secret(key: str, fallback: str) -> str:
    """st.secrets raises outright when no secrets file exists, so guard it."""
    try:
        return str(st.secrets[key])
    except Exception:
        return fallback


ADMIN_CODE = _secret("admin_code", "bppkn2026")


# ------------------------------------------------------------ session helpers

def _init_state() -> None:
    qp = st.query_params
    if "lang" not in st.session_state:
        st.session_state.lang = qp.get("lang", "bm")
    if "mode" not in st.session_state:
        st.session_state.mode = qp.get("mode", "light")
    # Checked on every run, not just the first: a stale URL or an old session
    # must not be able to wedge the app on an unknown value.
    if st.session_state.lang not in L.LANGS:
        st.session_state.lang = "bm"
    if st.session_state.mode not in T.MODES:
        st.session_state.mode = "light"
    if "iso" not in st.session_state:
        st.session_state.iso = S.current_week()
    st.session_state.setdefault("is_admin", False)


def _remember_prefs() -> None:
    """Mirror language and theme into the URL so a reload keeps them."""
    st.query_params["lang"] = st.session_state.lang
    st.query_params["mode"] = st.session_state.mode


def _nudge(delta: int) -> None:
    y, w = st.session_state.iso
    st.session_state.iso = S.shift_week(y, w, delta)


_init_state()
lang: str = st.session_state.lang
mode: str = st.session_state.mode
iso_year, iso_week = st.session_state.iso

st.markdown(T.css(mode), unsafe_allow_html=True)

staff = S.list_staff()
grid = S.status_matrix(iso_year, iso_week, staff)


def tr(key: str, **kw) -> str:
    return L.t(key, lang, **kw)


# -------------------------------------------------------------------- sidebar

with st.sidebar:
    st.markdown(f"### {tr('sb_week')}")
    st.caption(f"{tr('week')} {iso_week:02d} · {L.week_range_label(iso_year, iso_week, lang)}")
    a, b = st.columns(2)
    a.button(tr("prev_week"), width="stretch", on_click=_nudge, args=(-1,))
    b.button(tr("next_week"), width="stretch", on_click=_nudge, args=(1,))
    if st.button(tr("this_week"), width="stretch"):
        st.session_state.iso = S.current_week()
        st.rerun()

    st.divider()
    st.markdown(f"### {tr('sb_display')}")
    st.radio(
        tr("lang_label"),
        L.LANGS,
        format_func=lambda c: L.LANG_NAME[c],
        horizontal=True,
        key="lang",
        on_change=_remember_prefs,
    )
    st.radio(
        tr("mode_label"),
        T.MODES,
        format_func=lambda m: tr(f"mode_{m}"),
        horizontal=True,
        key="mode",
        on_change=_remember_prefs,
    )

    st.divider()
    st.markdown(f"### {tr('sb_policy')}")
    st.caption(tr("policy_text", n=S.MAX_WFH_PER_WEEK))

    st.divider()
    st.markdown(f"### {tr('sb_admin')}")
    if st.session_state.is_admin:
        st.caption(tr("admin_on"))
        if st.button(tr("admin_close"), width="stretch"):
            st.session_state.is_admin = False
            st.rerun()
    else:
        code = st.text_input(tr("admin_code"), type="password",
                             label_visibility="collapsed", placeholder=tr("admin_code"))
        if st.button(tr("admin_open"), width="stretch"):
            if code == ADMIN_CODE:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error(tr("admin_bad"))

    st.divider()
    frames = S.export_frames()
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        frames["staff"].to_excel(xw, sheet_name="staff", index=False)
        frames["entry"].to_excel(xw, sheet_name="entry", index=False)
    st.download_button(
        tr("backup_dl"),
        data=buf.getvalue(),
        file_name=f"sandaran_bdr_bppkn_{S.today():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )
    st.caption(tr("backup_hint"))


# ------------------------------------------------------------------- masthead

st.markdown(T.masthead(iso_year, iso_week, lang), unsafe_allow_html=True)
st.markdown(T.day_strip(grid, staff, iso_year, iso_week, lang, mode),
            unsafe_allow_html=True)

tabs = st.tabs([tr("tab_board"), tr("tab_mine"), tr("tab_summary"), tr("tab_dir")])


# ---------------------------------------------------------- 1. the board view

with tabs[0]:
    td = S.today()
    week_days = S.week_dates(iso_year, iso_week)
    if any(week_days[wd] == td for wd in S.WORK_WEEKDAYS):
        st.caption(tr("today_note", day=L.DAY_FULL[lang][td.isoweekday()],
                      date=L.date_label(td, lang)))
    else:
        st.caption(tr("other_week", date=L.date_label(td, lang)))

    st.markdown(T.roster(grid, staff, iso_year, iso_week, lang), unsafe_allow_html=True)
    st.markdown(T.legend(lang, mode), unsafe_allow_html=True)

    stamp = S.last_updated(iso_year, iso_week) or tr("no_records")
    st.markdown(
        f'<div class="stamp">{tr("last_update", stamp=stamp)} &nbsp;·&nbsp; '
        f'{tr("n_officers", n=len(staff))}</div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------ 2. edit your own week

with tabs[1]:
    if staff.empty:
        st.info(tr("dir_empty"))
    else:
        options = staff["id"].tolist()
        picked = st.selectbox(
            tr("pick_name"),
            options,
            format_func=lambda i: f"{staff.loc[staff['id'] == i, 'name'].iloc[0]}"
                                  f"  ·  {staff.loc[staff['id'] == i, 'section'].iloc[0]}",
            key="me",
        )
        current = S.person_week(picked, iso_year, iso_week)
        days = S.week_dates(iso_year, iso_week)

        st.markdown(
            f'<div class="panel-h" style="margin-top:14px">{tr("week")} {iso_week:02d} '
            f'&middot; {L.week_range_label(iso_year, iso_week, lang)}</div>',
            unsafe_allow_html=True,
        )

        plan, notes = {}, {}
        cols = st.columns(5)
        for col, wd in zip(cols, S.WORK_WEEKDAYS):
            with col:
                d = days[wd]
                st.markdown(
                    f"**{L.DAY_FULL[lang][wd]}**  \n"
                    f"<span style='font-family:var(--mono);font-size:10.5px;"
                    f"color:var(--ink-45)'>{d.day:02d}.{d.month:02d}.{d.year}</span>",
                    unsafe_allow_html=True,
                )
                allowed = ([S.OFFICE, S.WFH, S.LEAVE, S.DUTY] if wd in S.WFH_WEEKDAYS
                           else [S.OFFICE, S.LEAVE, S.DUTY])
                cur_status = current[wd][0]
                if cur_status not in allowed:
                    cur_status = S.OFFICE
                plan[wd] = st.radio(
                    L.DAY_FULL[lang][wd],
                    allowed,
                    index=allowed.index(cur_status),
                    format_func=lambda s: L.STATUS_LABEL[lang][s],
                    key=f"st_{picked}_{iso_year}_{iso_week}_{wd}",
                    label_visibility="collapsed",
                )
                notes[wd] = st.text_input(
                    tr("note_ph"),
                    value=current[wd][1],
                    key=f"nt_{picked}_{iso_year}_{iso_week}_{wd}",
                    placeholder=tr("note_ph"),
                    label_visibility="collapsed",
                )

        used = sum(1 for s in plan.values() if s == S.WFH)
        left = S.MAX_WFH_PER_WEEK - used
        if used > S.MAX_WFH_PER_WEEK:
            st.warning(tr("quota_over", used=used, over=used - S.MAX_WFH_PER_WEEK))
        elif left:
            st.caption(tr("quota_used", used=used, max=S.MAX_WFH_PER_WEEK, left=left))
        else:
            st.caption(tr("quota_full"))

        if st.button(tr("save_mine"), type="primary"):
            problems = L.validation_messages(plan, lang)
            if problems:
                for p in problems:
                    st.error(p)
            else:
                S.save_person_week(picked, iso_year, iso_week, plan, notes)
                name = staff.loc[staff["id"] == picked, "name"].iloc[0]
                st.success(tr("saved_mine", name=name, week=f"{iso_week:02d}"))
                st.rerun()


# ------------------------------------------------------------- 3. the summary

with tabs[2]:
    left_col, right_col = st.columns([1, 1], gap="medium")

    with left_col:
        st.markdown(f'<div class="panel-h">{tr("by_section")}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="panel">'
            f'{T.tally(grid, staff, "section", iso_year, iso_week, lang, mode)}</div>',
            unsafe_allow_html=True)

        st.markdown(f'<div class="panel-h">{tr("by_day")}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="panel">'
            f'{T.tally(grid, staff, "day", iso_year, iso_week, lang, mode)}</div>',
            unsafe_allow_html=True)

    with right_col:
        st.markdown(f'<div class="panel-h">{tr("coverage")}</div>', unsafe_allow_html=True)
        st.markdown(T.coverage_flags(grid, staff, iso_year, iso_week, lang),
                    unsafe_allow_html=True)

        st.markdown(f'<div class="panel-h">{tr("unused_head")}</div>', unsafe_allow_html=True)
        rows = []
        for r in staff.itertuples(index=False):
            n = int((grid.loc[r.id] == S.WFH).sum())
            if n < S.MAX_WFH_PER_WEEK:
                rows.append([r.name, r.section, n, S.MAX_WFH_PER_WEEK - n])
        if rows:
            st.markdown(
                T.flat_table([tr("th_name"), tr("th_section"), tr("th_wfh_days"),
                              tr("th_left")], rows, numeric={2, 3}),
                unsafe_allow_html=True)
        else:
            st.caption(tr("unused_none"))

    st.divider()
    st.markdown(f'<div class="panel-h">{tr("dl_week")}</div>', unsafe_allow_html=True)
    short = L.STATUS_SHORT[lang]
    wide = grid.rename(columns={wd: L.DAY_FULL[lang][wd] for wd in S.WORK_WEEKDAYS})
    wide = wide.map(lambda s: short.get(s, s))
    wide = staff.set_index("id")[["name", "position", "section"]].join(wide)
    wide.columns = ([tr("th_name"), tr("th_post"), tr("th_section")]
                    + [L.DAY_FULL[lang][wd] for wd in S.WORK_WEEKDAYS])
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        wide.to_excel(xw, sheet_name=f"{tr('week')} {iso_week}", index=False)
    c1, c2 = st.columns(2)
    c1.download_button(
        "Excel", data=out.getvalue(),
        file_name=f"jadual_bdr_bppkn_M{iso_week:02d}_{iso_year}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )
    c2.download_button(
        "CSV", data=wide.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"jadual_bdr_bppkn_M{iso_week:02d}_{iso_year}.csv",
        mime="text/csv", width="stretch",
    )
    st.markdown(
        T.flat_table(list(wide.columns), wide.values.tolist()),
        unsafe_allow_html=True)


# ------------------------------------------------------ 4. directory and admin

with tabs[3]:
    if not st.session_state.is_admin:
        st.info(tr("dir_locked"))
        st.markdown(
            T.flat_table([tr("th_name"), tr("th_post"), tr("th_section")],
                         staff[["name", "position", "section"]].values.tolist()),
            unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="panel-h">{tr("dir_edit")}</div>', unsafe_allow_html=True)
        st.caption(tr("dir_help"))
        sections = sorted(set(staff["section"].dropna()) | {"Lain-lain"})
        editor = st.data_editor(
            staff[["id", "name", "position", "section"]],
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "name": st.column_config.TextColumn(tr("th_name"), required=True,
                                                    width="large"),
                "position": st.column_config.TextColumn(tr("th_post"), width="medium"),
                "section": st.column_config.SelectboxColumn(tr("th_section"),
                                                            options=sections,
                                                            width="medium"),
            },
            key="dir_editor",
        )
        if st.button(tr("dir_save"), type="primary"):
            res = S.save_staff(editor)
            st.success(tr("dir_saved", ins=res["inserted"], upd=res["updated"],
                          rem=res["removed"]))
            st.rerun()

        st.divider()
        st.markdown(f'<div class="panel-h">{tr("week_tools")}</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.caption(tr("copy_hint"))
            if st.button(tr("copy_btn"), width="stretch"):
                src = S.shift_week(iso_year, iso_week, -1)
                n = S.copy_week(src, (iso_year, iso_week))
                st.success(tr("copied", n=n, week=f"{src[1]:02d}"))
                st.rerun()
        with c2:
            st.caption(tr("clear_hint"))
            confirm = st.checkbox(tr("clear_confirm", week=f"{iso_week:02d}"))
            if st.button(tr("clear_btn"), width="stretch", disabled=not confirm):
                n = S.clear_week(iso_year, iso_week)
                st.success(tr("cleared", n=n))
                st.rerun()

        st.divider()
        st.markdown(f'<div class="panel-h">{tr("restore_head")}</div>',
                    unsafe_allow_html=True)
        st.caption(tr("restore_hint"))
        up = st.file_uploader(tr("restore_file"), type="xlsx",
                              label_visibility="collapsed")
        if up is not None and st.button(tr("restore_btn")):
            try:
                book = pd.read_excel(up, sheet_name=None)
                S.import_frames(book["staff"], book["entry"])
                st.success(tr("restored"))
                st.rerun()
            except Exception as exc:
                st.error(tr("restore_bad", err=exc))
