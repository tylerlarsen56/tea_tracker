# Tea Price Tracker

A personal price-per-gram tracker for nine Shopify-based tea merchants,
with a weekly email digest and a browser dashboard for filtering,
visualizing, and building a "cart" of what to order next.

## How it fits together

```
 Windows PC (runs weekly via Task Scheduler)
 ┌───────────────────────────────────────────────────────────┐
 │  run_tea_tracker.bat                                       │
 │      └── tea_price_tracker.py                              │
 │            ├── scrapes 9 Shopify sites                     │
 │            ├── writes output/tea_prices_YYYY-MM-DD.csv     │
 │            ├── tea_db.py: trims + inserts into              │
 │            │     tea_prices.db (SQLite)                     │
 │            ├── git_publish.py: copies tea_prices.db into    │
 │            │     the dashboard repo, commits, pushes  ──────┼──┐
 │            └── emails you the weekly top-10 deals            │  │
 └────────────────────────────────────────────────────────────┘  │
                                                                    ▼
                                                      GitHub repo (dashboard)
                                                      ┌───────────────────────┐
                                                      │ tea_dashboard.html    │
                                                      │ tea_prices.db         │◄── published here
                                                      └──────────┬────────────┘
                                                                 │ served by
                                                                 ▼
                                                      GitHub Pages (public URL)
                                                      opening it auto-loads
                                                      tea_prices.db, no click
                                                      required
```

The scraper and the database live and run **locally**, on your own
machine, on a schedule. Only the trimmed `tea_prices.db` file ever gets
pushed anywhere - the scraping code, your email address, and your Gmail
app password never leave your PC.

## Files

| File | Purpose |
|---|---|
| `tea_price_tracker.py` | Weekly scraper. Writes a CSV, updates `tea_prices.db`, publishes it to git, sends the email. |
| `config.py` | Your Gmail sender/recipient + app password, and (optionally) the path to your dashboard git repo. **Never commit this file anywhere.** |
| `tea_db.py` | SQLite storage: add/remove/trim/list runs, plus the trend-query helpers the dashboard's "what's new" feature is built on. |
| `git_publish.py` | Copies `tea_prices.db` into your dashboard repo and does `git add` / `commit` / `push`, safely and idempotently. |
| `migrate_csvs_to_db.py` | One-time (or occasional) bulk-import of `output/*.csv` history into a `.db` file. |
| `run_tea_tracker.bat` | What Task Scheduler actually runs each week. |
| `tea_dashboard.html` | The dashboard. Fully self-contained, runs entirely in your browser - no server, no build step. |

## One-time setup

1. **Python deps:** `pip install requests`
2. **Gmail app password:** create one at
   [myaccount.google.com](https://myaccount.google.com) → Security →
   2-Step Verification → App Passwords (requires 2FA to be on), then
   fill in `config.py`.
3. **Test the scraper by hand:** `python tea_price_tracker.py` from this
   folder. Check `tea_tracker.log` and confirm the email arrives.
4. **Weekly automation:** open Task Scheduler → Create Task →
   - Trigger: Weekly, whatever day/time you like.
   - Action: `run_tea_tracker.bat`, with "Start in" set to this folder.
   - Under Settings, check "Run task as soon as possible after a
     scheduled start is missed" and consider "Wake the computer to run
     this task" if your PC sleeps.
   - Under General, "Run whether user is logged on or not" is more
     reliable, but see the git note below before you turn that on.

## Publishing the dashboard's data automatically

1. Put `tea_dashboard.html` in its own git repo and enable GitHub Pages
   for it (Settings → Pages).
2. Clone that repo somewhere on the same PC, e.g.
   `C:\Users\you\tea-dashboard-site`.
3. In `config.py`, set `GIT_REPO_DIR` to that folder's path.
4. From that folder, run `git push` **by hand once**, with nothing
   changed, to confirm it completes with **no login prompt**. If it
   asks for credentials, either switch the remote to SSH with a
   passphrase-less key (or a loaded `ssh-agent`) or make sure Windows
   Credential Manager has your HTTPS credentials cached - a scheduled
   task can't answer an interactive prompt.
5. Run `tea_price_tracker.py` by hand once more and check
   `tea_tracker.log` for `Pushed updated tea_prices.db` to confirm the
   whole chain works before trusting it to run unattended weekly.

**A note on "Run whether user is logged on or not":** that setting runs
the task under a different Windows security context than your normal
login, which may not have access to your cached git credentials even if
step 4 above worked fine when you tested it interactively. If the push
step starts failing only once you switch to that setting, that's almost
certainly why - either use "Run only when user is logged on" instead, or
switch to an SSH key stored somewhere that context can read.

## Data retention

`tea_prices.db` is intentionally kept small: every run trims anything
older than the 2 most recent prior sessions before adding its own data,
so the database holds about 3 weeks of history at any time (see
`tea_db.trim_old_sessions()`). This keeps it cheap to commit to git every
week. **The CSVs in `output/` are never trimmed** - they're your real,
permanent history. If you ever want a full, untrimmed database for your
own analysis, run `migrate_csvs_to_db.py` against a separate output
`.db` path rather than relying on the live `tea_prices.db`.

## Security

- `config.py` contains a live credential. Add it to `.gitignore` (see
  the one in this folder) in **every** repo it could conceivably end up
  in, and never email, upload, or screenshot it.
- If this app password is ever exposed (uploaded, pasted into a chat,
  committed by accident, etc.), revoke it immediately at
  myaccount.google.com and generate a new one.
- The dashboard repo/Pages site is public by default. `tea_prices.db`
  (tea listings and prices) isn't especially sensitive, but it will be
  visible to anyone who finds the URL - make the repo private (GitHub
  Pages works with private repos on paid plans) if that matters to you.

## Local testing of the dashboard

The auto-load feature uses `fetch()`, which browsers block against
`file://` URLs for security reasons. Double-clicking `tea_dashboard.html`
to test it locally will NOT auto-load a nearby `tea_prices.db` - you'll
need to either use the manual "Load Database" button, or serve the
folder locally first, e.g.:

```
python -m http.server 8000
```

then open `http://localhost:8000/tea_dashboard.html` in a browser.
