# Papan Jadual Bekerja Dari Rumah — BPPKN

A shared work-from-home roster for the 25 officers of Bahagian Perisikan dan
Pengurusan Krisis Negara. Staff set their own days; the Pengarah reads the
board. Policy is enforced in code: **up to 2 days per week, Tuesday to
Thursday only.** Monday and Friday do not offer the WFH option at all.

The board always opens on the current ISO week in Malaysian time, no matter
where the server is.

---

## 1. Run it on your own machine (2 minutes)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`. On first run the app creates `wfh.db` and
loads the 25 names from `staff_seed.csv`. Nothing else to set up.

## 2. Run it on the office network (recommended)

This keeps the roster inside MKN — no public URL, no external accounts, no
staff names on the open internet.

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Find your machine's address with `ipconfig` (Windows) or `hostname -I`
(Linux), then circulate `http://<that-address>:8501`. Colleagues open it in
any browser. The machine has to stay on and awake while people are using it.

If you want it always available, ask IT to run the same command on a server
that is already on the network.

## 3. Deploy to Streamlit Community Cloud (public link)

Do read section 5 before choosing this route.

1. Create a GitHub repository and push this folder to it.
   ```bash
   git init && git add . && git commit -m "Papan jadual BDR BPPKN"
   git branch -M main
   git remote add origin https://github.com/<you>/bppkn-wfh.git
   git push -u origin main
   ```
   `.gitignore` already keeps `wfh.db` and `secrets.toml` out of the repo.
2. Go to **share.streamlit.io** and sign in with that same GitHub account.
3. **Create app** → **Deploy a public app from GitHub**.
4. Repository: your repo. Branch: `main`. Main file path: `app.py`.
5. **Advanced settings** → Secrets, paste:
   ```toml
   admin_code = "pick-something-else"
   ```
6. **Deploy**. After a minute you get `https://<name>.streamlit.app` — that
   is the link to share with the bahagian.

To change the app's name later: **Settings → General → App URL**.

## 4. The admin code

The Direktori tab and the week tools sit behind a code. The built-in default
is `bppkn2026` — **change it.**

- Deployed on Streamlit Cloud: set `admin_code` in Secrets (step 5 above).
- Running locally: create `.streamlit/secrets.toml` containing
  `admin_code = "your-code"`. That file is gitignored.

Everything else — viewing the board, setting your own days — needs no code,
so people can use it without an account.

## 5. Two things to weigh before making it public

**It is a public URL.** Anyone holding the link can read the board, and the
board is a named BPPKN staff list showing where each officer is on each day,
including police and military officers by rank. Streamlit Community Cloud has
no password option on the free tier. Worth checking against your own
policy before it goes out; option 2 above avoids the question entirely.

**Community Cloud storage is temporary.** The container filesystem is wiped
when the app reboots, redeploys, or sleeps after inactivity, and `wfh.db`
goes with it. Schedules would be lost. Two ways to handle it:

- *Low effort:* use **Muat turun sandaran** in the sidebar each Friday. To
  restore, an admin uploads that file under Direktori → Pulihkan dari
  sandaran. Fine if losing at most one week is acceptable.
- *Proper fix:* move storage off the container — see section 8.

Running on the office network (option 2) has neither problem: the database is
just a file on that machine.

## 6. Language and theme

All the text lives in `i18n.py`, two entries per line:

```python
"save_mine": {"bm": "Simpan jadual saya", "en": "Save my schedule"},
```

Correct a wording by editing the string; add a third language by adding a
code to `LANGS`, a name to `LANG_NAME`, and a third key to every entry
(`DAY_FULL`, `DAY_ABBR`, `MONTH`, `STATUS_SHORT` and `STATUS_LABEL` too). To
open in English by default, change the fallback in `app.py`'s `_init_state`
from `"bm"` to `"en"`.

The two palettes are at the top of `theme.py` in `PALETTES`. Every colour the
app draws comes from there, so changing `brass` in both blocks restyles the
accent everywhere. The app declares its own colours for Streamlit's widgets
rather than inheriting them, which is what keeps text readable whichever base
theme a viewer's browser or Streamlit account happens to prefer.

One known limit: the directory editor in the Direktori tab is a
`st.data_editor`, which draws into a canvas that follows Streamlit's own base
theme rather than this app's switch. It stays light while the rest of the page
goes dark. It is admin-only and fully functional, so this is cosmetic. Every
other table on the page is drawn as HTML and does follow the switch.

## 7. Changing the policy

Everything lives at the top of `store.py`:

```python
WFH_WEEKDAYS = (2, 3, 4)      # Tue, Wed, Thu — ISO numbering, Monday = 1
MAX_WFH_PER_WEEK = 2
```

Allowing Monday too is `(1, 2, 3, 4)`. Three days a week is
`MAX_WFH_PER_WEEK = 3`. The day cards, the radio buttons, and the save-time
validation all read these, so one edit is enough.

Statuses are defined just above them if you need to add, say, *Kursus* or
*Bertugas Parlimen* — add the constant, a label, and a colour in `theme.py`
under `_SW` and the `.c-XXX` CSS rules.

## 8. Editing names

Direktori tab, with the admin code entered. It is a spreadsheet-style table:

- Type over a cell to correct a name, jawatan, or seksyen.
- Bottom row adds an officer. New officers automatically sort into their own
  seksyen rather than to the foot of the board.
- Select a row and delete it when someone transfers out. **This also deletes
  their schedule records** — take a backup first if you want the history.
- Row order sets the order on the board.

Press **Simpan direktori** to apply. `staff_seed.csv` is only read once, on
the very first run, so editing it later changes nothing — use the tab.

## 9. Making the data survive restarts

If you deploy publicly and want durable storage, the change is confined to
`store.py` — every read and write already goes through the functions there.

Google Sheets is usually the easiest, and gives you a copy you can open in
Excel. You need a Google Cloud service account, its JSON key in Streamlit
Secrets, and the sheet shared with the service-account email. Add
`st-gsheets-connection` to `requirements.txt`, then replace the bodies of
`week_entries`, `save_person_week`, `list_staff`, and `save_staff` with reads
and writes against two worksheets mirroring the `staff` and `entry` tables.

A free Postgres instance (Supabase, Neon) is the other route: keep the SQL
essentially as it is and swap the `connect()` function for a `psycopg`
connection built from a secret.

Tell me which you want and I will write it — it is a contained change, but it
needs testing against real credentials, so I would rather do it properly than
hand you something untested.

## 10. Files

| File | What it does |
|---|---|
| `app.py` | The four tabs and all the widgets |
| `store.py` | Database, policy rules, backup and restore |
| `theme.py` | The two palettes, and the HTML for the day cards and roster grid |
| `i18n.py` | Every piece of UI text, in Bahasa Melayu and English |
| `staff_seed.csv` | The 25 officers, read on first run only |
| `requirements.txt` | Three dependencies |
| `.streamlit/config.toml` | Colours, so Streamlit's own widgets match the board |
| `wfh.db` | Created on first run. Not in git. This is your data. |

The board reads `PEJABAT` (in office), `BDR` (bekerja dari rumah), `CUTI`, and
`LUAR` (tugas luar). Office days show as a faint dash so that the days
somebody is away are the ones your eye lands on.

One note on the directory as supplied: the source spreadsheet spelled several
admin posts *Pambantu Tadbir*; that is corrected to *Pembantu Tadbir* in
`staff_seed.csv`. Officer #13 was listed as "Reza" with no further name —
worth completing in the Direktori tab.
