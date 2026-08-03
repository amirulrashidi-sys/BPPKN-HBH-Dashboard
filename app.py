"""Papan Jadual Bekerja Dari Rumah — BPPKN, Majlis Keselamatan Negara.

Run locally:      streamlit run app.py
Share on the LAN: streamlit run app.py --server.address 0.0.0.0 --server.port 8501
"""

from __future__ import annotations

import io
from datetime import date

import pandas as pd
import streamlit as st

import store as S
import theme as T

st.set_page_config(
    page_title="Papan Jadual BDR · BPPKN",
    page_icon="🗓",
    layout="wide",
    initial_sidebar_state="expanded",
)

S.init_db()
st.markdown(T.CSS, unsafe_allow_html=True)

def _secret(key: str, fallback: str) -> str:
    """st.secrets raises outright when no secrets file exists, so guard it."""
    try:
        return str(st.secrets[key])
    except Exception:
        return fallback


ADMIN_CODE = _secret("admin_code", "bppkn2026")


# ------------------------------------------------------------ session helpers

def _init_state() -> None:
    if "iso" not in st.session_state:
        st.session_state.iso = S.current_week()
    st.session_state.setdefault("is_admin", False)


def _nudge(delta: int) -> None:
    y, w = st.session_state.iso
    st.session_state.iso = S.shift_week(y, w, delta)


_init_state()
iso_year, iso_week = st.session_state.iso
staff = S.list_staff()
grid = S.status_matrix(iso_year, iso_week, staff)


# -------------------------------------------------------------------- sidebar

with st.sidebar:
    st.markdown("### Minggu")
    st.caption(f"Minggu {iso_week:02d} · {S.week_range_label(iso_year, iso_week)}")
    a, b = st.columns(2)
    a.button("◀ Sebelum", width="stretch", on_click=_nudge, args=(-1,))
    b.button("Selepas ▶", width="stretch", on_click=_nudge, args=(1,))
    if st.button("Kembali ke minggu ini", width="stretch"):
        st.session_state.iso = S.current_week()
        st.rerun()

    st.divider()
    st.markdown("### Dasar")
    st.caption(
        f"Maksimum **{S.MAX_WFH_PER_WEEK} hari** bekerja dari rumah seminggu, "
        "**Selasa hingga Khamis** sahaja. Isnin dan Jumaat adalah hari wajib di pejabat."
    )

    st.divider()
    st.markdown("### Pentadbir")
    if st.session_state.is_admin:
        st.caption("Akses pentadbir dibuka.")
        if st.button("Tutup akses", width="stretch"):
            st.session_state.is_admin = False
            st.rerun()
    else:
        code = st.text_input("Kod pentadbir", type="password", label_visibility="collapsed",
                             placeholder="Kod pentadbir")
        if st.button("Buka akses", width="stretch"):
            if code == ADMIN_CODE:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Kod tidak sah.")

    st.divider()
    frames = S.export_frames()
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        frames["staff"].to_excel(xw, sheet_name="staff", index=False)
        frames["entry"].to_excel(xw, sheet_name="entry", index=False)
    st.download_button(
        "Muat turun sandaran",
        data=buf.getvalue(),
        file_name=f"sandaran_bdr_bppkn_{S.today():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )
    st.caption("Simpan sandaran ini setiap minggu.")


# ------------------------------------------------------------------- masthead

st.markdown(T.masthead(iso_year, iso_week), unsafe_allow_html=True)
st.markdown(T.day_strip(grid, staff, iso_year, iso_week), unsafe_allow_html=True)

tabs = st.tabs(["Papan Jadual", "Jadual Saya", "Ringkasan", "Direktori"])


# ---------------------------------------------------------- 1. the board view

with tabs[0]:
    td = S.today()
    if any(S.week_dates(iso_year, iso_week)[wd] == td for wd in S.WORK_WEEKDAYS):
        st.caption(f"Hari ini {S.DAY_FULL[td.isoweekday()] if td.isoweekday() <= 5 else ''} "
                   f"{S.date_label(td)}. Lajur hari ini ditanda kuning.")
    else:
        st.caption(f"Anda sedang melihat minggu lain. Hari ini {S.date_label(td)}.")

    st.markdown(T.roster(grid, staff, iso_year, iso_week), unsafe_allow_html=True)
    st.markdown(T.legend(), unsafe_allow_html=True)

    stamp = S.last_updated(iso_year, iso_week)
    st.markdown(
        f'<div class="stamp">Kemas kini terakhir: {stamp if stamp else "belum ada rekod"}'
        f' &nbsp;·&nbsp; {len(staff)} pegawai</div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------ 2. edit your own week

with tabs[1]:
    if staff.empty:
        st.info("Direktori masih kosong. Tambah nama di tab Direktori.")
    else:
        options = staff["id"].tolist()
        picked = st.selectbox(
            "Pilih nama anda",
            options,
            format_func=lambda i: f"{staff.loc[staff['id'] == i, 'name'].iloc[0]}"
                                  f"  ·  {staff.loc[staff['id'] == i, 'section'].iloc[0]}",
            key="me",
        )
        current = S.person_week(picked, iso_year, iso_week)
        days = S.week_dates(iso_year, iso_week)

        st.markdown(
            f'<div class="panel-h" style="margin-top:14px">Minggu {iso_week:02d} '
            f'&middot; {S.week_range_label(iso_year, iso_week)}</div>',
            unsafe_allow_html=True,
        )

        plan, notes = {}, {}
        cols = st.columns(5)
        for col, wd in zip(cols, S.WORK_WEEKDAYS):
            with col:
                d = days[wd]
                st.markdown(
                    f"**{S.DAY_FULL[wd]}**  \n"
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
                    S.DAY_FULL[wd],
                    allowed,
                    index=allowed.index(cur_status),
                    format_func=lambda s: S.STATUS_LABEL[s],
                    key=f"st_{picked}_{iso_year}_{iso_week}_{wd}",
                    label_visibility="collapsed",
                )
                notes[wd] = st.text_input(
                    "Catatan",
                    value=current[wd][1],
                    key=f"nt_{picked}_{iso_year}_{iso_week}_{wd}",
                    placeholder="Catatan",
                    label_visibility="collapsed",
                )

        used = sum(1 for s in plan.values() if s == S.WFH)
        left = S.MAX_WFH_PER_WEEK - used
        if used > S.MAX_WFH_PER_WEEK:
            st.warning(
                f"Melebihi kuota: {used} hari BDR dipilih. Tukar {used - S.MAX_WFH_PER_WEEK} "
                "hari kembali kepada *Di pejabat* sebelum menyimpan."
            )
        elif left:
            st.caption(f"{used} daripada {S.MAX_WFH_PER_WEEK} hari BDR digunakan. "
                       f"Baki {left} hari.")
        else:
            st.caption(f"Kedua-dua hari BDR telah digunakan.")

        if st.button("Simpan jadual saya", type="primary"):
            problems = S.validate_week(plan)
            if problems:
                for p in problems:
                    st.error(p)
            else:
                S.save_person_week(picked, iso_year, iso_week, plan, notes)
                name = staff.loc[staff["id"] == picked, "name"].iloc[0]
                st.success(f"Jadual {name} untuk minggu {iso_week:02d} disimpan.")
                st.rerun()


# ------------------------------------------------------------- 3. the summary

with tabs[2]:
    left, right = st.columns([1, 1], gap="medium")

    with left:
        st.markdown('<div class="panel-h">Taburan mengikut seksyen</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="panel">{T.tally(grid, staff, "section", iso_year, iso_week)}'
                    f'</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel-h">Taburan mengikut hari</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="panel">{T.tally(grid, staff, "day", iso_year, iso_week)}'
                    f'</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel-h">Liputan pejabat</div>', unsafe_allow_html=True)
        st.markdown(T.coverage_flags(grid, staff, iso_year, iso_week), unsafe_allow_html=True)

        st.markdown('<div class="panel-h">Pegawai belum penuh kuota BDR</div>',
                    unsafe_allow_html=True)
        unused = []
        for r in staff.itertuples(index=False):
            n = int((grid.loc[r.id] == S.WFH).sum())
            if n < S.MAX_WFH_PER_WEEK:
                unused.append({"Nama": r.name, "Seksyen": r.section,
                               "Hari BDR": n, "Baki": S.MAX_WFH_PER_WEEK - n})
        if unused:
            st.dataframe(pd.DataFrame(unused), hide_index=True, width="stretch")
        else:
            st.caption("Semua pegawai telah menggunakan kuota penuh.")

    st.divider()
    st.markdown('<div class="panel-h">Muat turun jadual minggu ini</div>', unsafe_allow_html=True)
    wide = grid.rename(columns={wd: S.DAY_FULL[wd] for wd in S.WORK_WEEKDAYS})
    wide = staff.set_index("id")[["name", "position", "section"]].join(wide)
    wide.columns = ["Nama", "Jawatan", "Seksyen"] + [S.DAY_FULL[wd] for wd in S.WORK_WEEKDAYS]
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        wide.to_excel(xw, sheet_name=f"Minggu {iso_week}", index=False)
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
    st.dataframe(wide, hide_index=True, width="stretch")


# ------------------------------------------------------ 4. directory and admin

with tabs[3]:
    if not st.session_state.is_admin:
        st.info("Masukkan kod pentadbir di bar sisi untuk menyunting direktori.")
        st.dataframe(
            staff[["name", "position", "section"]].rename(
                columns={"name": "Nama", "position": "Jawatan", "section": "Seksyen"}),
            hide_index=True, width="stretch",
        )
    else:
        st.markdown('<div class="panel-h">Sunting direktori</div>', unsafe_allow_html=True)
        st.caption(
            "Tambah baris untuk pegawai baharu, sunting nama atau jawatan terus dalam jadual, "
            "dan buang baris untuk pegawai yang bertukar. Susunan baris menentukan susunan "
            "papan jadual. Membuang seorang pegawai akan membuang rekod jadual beliau juga."
        )
        sections = sorted(set(staff["section"].dropna()) | {"Lain-lain"})
        editor = st.data_editor(
            staff[["id", "name", "position", "section"]],
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "name": st.column_config.TextColumn("Nama", required=True, width="large"),
                "position": st.column_config.TextColumn("Jawatan", width="medium"),
                "section": st.column_config.SelectboxColumn(
                    "Seksyen", options=sections, width="medium"),
            },
            key="dir_editor",
        )
        if st.button("Simpan direktori", type="primary"):
            res = S.save_staff(editor)
            st.success(
                f"Direktori dikemas kini: {res['inserted']} baharu, "
                f"{res['updated']} disunting, {res['removed']} dibuang."
            )
            st.rerun()

        st.divider()
        st.markdown('<div class="panel-h">Alat minggu</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Salin jadual minggu sebelum ke minggu ini.")
            if st.button("Salin dari minggu sebelum", width="stretch"):
                src = S.shift_week(iso_year, iso_week, -1)
                n = S.copy_week(src, (iso_year, iso_week))
                st.success(f"{n} rekod disalin dari minggu {src[1]:02d}.")
                st.rerun()
        with c2:
            st.caption("Kosongkan semua rekod bagi minggu yang sedang dipaparkan.")
            confirm = st.checkbox(f"Saya pasti mahu kosongkan minggu {iso_week:02d}")
            if st.button("Kosongkan minggu ini", width="stretch", disabled=not confirm):
                n = S.clear_week(iso_year, iso_week)
                st.success(f"{n} rekod dibuang.")
                st.rerun()

        st.divider()
        st.markdown('<div class="panel-h">Pulihkan dari sandaran</div>', unsafe_allow_html=True)
        st.caption("Memuat naik sandaran akan menggantikan semua data semasa.")
        up = st.file_uploader("Fail sandaran .xlsx", type="xlsx", label_visibility="collapsed")
        if up is not None and st.button("Pulihkan sekarang"):
            try:
                book = pd.read_excel(up, sheet_name=None)
                S.import_frames(book["staff"], book["entry"])
                st.success("Data dipulihkan.")
                st.rerun()
            except Exception as exc:
                st.error(f"Sandaran tidak dapat dibaca: {exc}")
