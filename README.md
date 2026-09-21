# Tea Price Tracker

A personal price-per-gram tracker for thirteen online tea merchants, with a
weekly email digest and a browser dashboard for filtering, visualizing, and
building a "cart" of what to order next.

## How it fits together

```
 Windows PC (runs weekly via Task Scheduler)
 ┌───────────────────────────────────────────────────────────┐
 │  run_tea_tracker.bat                                      │
 │      └── tea_price_tracker.py                             │
 │            ├── site_adapters.py: reads 13 shops across    │
 │            │     4 platforms into one common shape        │
 │            ├── writes output/tea_prices_YYYY-MM-DD.csv    │
 │            ├── tea_db.py: trims + inserts into            │
 │            │     tea_prices.db (SQLite)                   │
 │            ├── git_publish.py: copies tea_prices.db into  │
 │            │     the dashboard repo, commits, pushes  ────┼──┐
 │            └── emails you the weekly top-10 deals         │  │
 └───────────────────────────────────────────────────────────┘  │
                                                                ▼
                                                      GitHub repo (dashboard)
                                                      ┌───────────────────────┐
                                                      │ index.html            │
                                                      │ tea_prices.db         │◄── published here
                                                      └──────────┬────────────┘
                                                                 │ served by
                                                                 ▼
                                                      GitHub Pages (public URL)
                                                      opening it auto-loads
                                                      tea_prices.db, no click
                                                      required
```

The scraper and the database live and run **locally**, on a schedule. Only
the trimmed `tea_prices.db` is ever pushed anywhere - the scraping code, your
email address and your Gmail app password never leave your PC.

## Files

| File | Purpose |
|---|---|
| `tea_price_tracker.py` | Weekly scraper. Classifies, writes a CSV, updates `tea_prices.db`, publishes it to git, sends the email. |
| `site_adapters.py` | One fetcher per shop **platform** - Shopify, Magento (Verdant Tea), Sitefinity (TWG Tea), and Mei Leaf's bespoke storefront. The only code that knows how a given shop serves its catalog; everything after it is shared. |
| `config.py` | Your Gmail sender/recipient + app password, and (optionally) the path to your dashboard git repo. **Never commit this file anywhere.** |
| `tea_db.py` | SQLite storage: add/remove/trim/list runs, the trend-query helpers the dashboard's "what's new" feature is built on, and `write_dashboard_copy()` / `gzip_file()`, which build the slimmed, gzipped copy that actually gets published. |
| `git_publish.py` | Copies the published database files into your dashboard repo and does `git add` / `commit` / `push`, safely and idempotently. |
| `migrate_csvs_to_db.py` | One-time (or occasional) bulk-import of `output/*.csv` history into a `.db` file. |
| `run_tea_tracker.bat` | What Task Scheduler actually runs each week. |
| `index.html` | The dashboard. Fully self-contained, runs entirely in your browser - no server, no build step. It is responsive: on narrow screens the filter sidebar collapses behind a "Filters" button and the listing rows stack. Being named `index.html` is what makes GitHub Pages serve it at the site root, with no filename in the URL. |

### Tea types

Every listing is filed as **Raw Puer, Ripe Puer, Heicha, Oolong, Black, White,
Green, Yellow, Purple, Herbal** or **Other**. `Herbal` is everything a tea shop
sells that isn't Camellia sinensis - rooibos, mate, tisanes, flower and
wellness blends. They have a weight and a price per gram like any other
listing, they just aren't a tea *type*, and mixing them into `Other` hid both
them and the listings that genuinely couldn't be classified.

Two things decide the answer, and they are deliberately not treated alike:

- **Type keywords** say outright what a tea is - "white tea", "shou cha",
  "dark tea". These are checked first, over the title, then over the shop's own
  product type and tags.
- **Varietal keywords** only say what the leaf, grade or estate is called -
  "tieguanyin", "biluochun", "shou mei". A famous cultivar is routinely
  processed into a different type and the title says so, so these are checked
  *last*: "Laoshan Biluochun Black" is a black tea, "An Ji Bai Cha" is a green
  one despite reading "white tea", and "2026 Rou Gui Wuyi Black Tea" is black,
  not oolong.

Between the two sit `SITE_METADATA_CATEGORY_OVERRIDES`, for shops whose own
shelf naming is the only per-product signal there is: TWG calls rooibos
"Theine-Free Red Tea" and puer "Matured Tea", Mei Leaf tags every product
`tea type <x>`, and Farmerleaf files 256 listings under one flat "Pu-erh tea".

### Form factors

Every variant is tagged with a physical form: **Flowering Tea, Dragon Ball,
Fruit-stuffed, Tea Resin, Bamboo Tube, Tea Bag, Sample, Cake Portion, Tong,
Mini, Whole Cake, Loose Leaf** or **Other/Unspecified**. Classification reads
the product/variant title first, then falls back to the shop's own `Shape_*`
tags or product type, then to a per-site default. `Cake Portion` and `Sample`
are split by a 50 g threshold when a variant is smaller than another size of
the same product. Teaware, Tea Tools, Tea Pet and **Merch** (hoodies,
t-shirts, posters and other apparel/prints some shops sell) are excluded from
the tea dataset entirely and never get a price-per-gram.

**How a listing is ruled out as tea.** Keywords are matched as *words*, not
substrings - "tea mat" must not fire inside "20 Years' aged Tea Material" or
inside "Matcha". Beyond that there is a **tea veto**: if a shop hasn't shelved
a product as an accessory and its own product type or tags name a tea type,
it's tea, and no keyword in the title overrules that. Yunnan Sourcing's
"Medusa's Teapot" Ripe Pu-erh cake is a cake, King Tea Mall's
"Shou Mei ... 100g/Tin Can" is a white tea, and TWG's "Mate" is a herbal
infusion. Genuine accessories are unaffected, because shops tag those as
accessories. Apparel is the one exception, checked ahead of the veto: a
sticker pack is a sticker pack even when the shop types it "Sheng Puerh".

### Sites and platforms

| Shop | Platform | How its catalog is read |
|---|---|---|
| Mountain Stream Teas, white2tea, Yunnan Sourcing, Jesse's Tea House, Crimson Lotus Tea, Farmerleaf, Path of Cha, Meimei Fine Teas, The Chinese Tea Shop, Red Blossom Tea Company | Shopify | the public `/products.json` and `/collections.json` feeds |
| Verdant Tea | Magento 2 | its public `/graphql` endpoint (no key needed - it is what the storefront itself uses) |
| TWG Tea | Sitefinity | `/sitemap-en.xml` for the catalog, then a product API that returns up to ~100 SKUs per call, with each size's real net weight |
| Mei Leaf | bespoke | server-rendered HTML, parsed with BeautifulSoup - the one shop with no feed of any kind |

**Why one script and not one per platform.** Only the *fetch* differs between
shops. Weight parsing, form factors, teaware detection, tasting notes,
price-per-gram, the CSV, the database, the email and the git publish are all
platform-independent, and they are the part that has taken real work to get
right. Four scripts would mean four copies of that logic and four places for it
to drift: improve a form-factor rule and three sites would silently keep the old
one. So each platform gets an *adapter* in `site_adapters.py` whose only job is
to return products in one common shape, and every decision after that happens
once, identically, for all thirteen shops.

Two things genuinely can't be the same everywhere:

- **Checkout links.** The dashboard's "Check Out" button builds a Shopify cart
  permalink (`{shop}/cart/{variant_id}:{qty}`). No other platform reads such a
  URL, so listings from Verdant, TWG and Mei Leaf carry no variant id and the
  button tells you to use the listing links instead.
- **Crawl speed.** TWG's `robots.txt` asks for a 5-second delay, which its entry
  in `SITES` honors. It only makes about fifteen requests, so that costs about a
  minute. Mei Leaf is the slow one - roughly 350 product pages, about ten
  minutes - because a shop with no feed leaves no alternative.

## One-time setup

1. **Python deps:** `pip install -r requirements.txt` (`requests`, plus
   `beautifulsoup4` - needed only for Mei Leaf, the one shop with no product
   feed; without it that site is skipped and the other twelve still run)
2. **Gmail app password:** create one at
   [myaccount.google.com](https://myaccount.google.com) → Security →
   2-Step Verification → App Passwords (requires 2FA to be on), then
   fill in `config.py`.
3. **Test the scraper by hand:** `python tea_price_tracker.py` from this
   folder. Check `tea_tracker.log` and confirm the email arrives.
4. **Weekly automation:** open Task Scheduler → Create Task →
   - Trigger: Weekly, whatever day/time you like.
   - Action: `run_tea_tracker.bat`, with "Start in" set to this folder.
   - Under Settings, check "Run task as soon as possible after a missed
     start", and "Wake the computer to run this task" if your PC sleeps.
   - Under General, "Run whether user is logged on or not" is more
     reliable, but see the git note below first.

## Publishing the dashboard's data automatically

1. Put `index.html` in its own git repo and enable GitHub Pages (Settings → Pages).
2. Clone that repo on the same PC, e.g. `C:\Users\you\tea-dashboard-site`.
3. In `config.py`, set `GIT_REPO_DIR` to that folder's path.
4. From that folder, run `git push` **by hand once**, with nothing changed,
   to confirm it completes with **no login prompt** - a scheduled task
   can't answer one. If it asks for credentials, switch the remote to SSH
   with a passphrase-less key (or a loaded `ssh-agent`), or cache your
   HTTPS credentials in Windows Credential Manager.
5. Run `tea_price_tracker.py` by hand once more and check `tea_tracker.log`
   for `Pushed updated tea_prices.db` before trusting it to run weekly.

### Sleep

A full run takes long enough that a laptop left alone will idle-sleep partway
through, and every site still queued then fails with `ConnectionResetError
(10054)`. The script holds that off itself: `keep_system_awake()` asks Windows
not to idle-sleep while a run is in progress and releases the request as soon
as it finishes (or crashes - the request dies with the process). The log says
so at both ends:

```
Holding off system sleep for the duration of this run.
...
Released the stay-awake request - normal sleep rules apply again.
```

It deliberately does NOT keep the screen on, and it can only stop an *idle*
sleep: closing the lid, picking Sleep from the Start menu, or a critically low
battery still puts the machine down mid-run. On anything other than Windows it
logs one line and does nothing.

**A note on "Run whether user is logged on or not":** that setting runs the
task under a different Windows security context, which may not reach the git
credentials cached for your normal login - even if step 4 worked fine
interactively. If the push starts failing only after you switch it on, that's
why: use "Run only when user is logged on", or an SSH key that context can
read.

## The weekly email list

The dashboard's **Join the Email List** button opens the visitor's own mail app
with a pre-filled request - the page has no server, so nothing is collected
there. When one of those arrives, paste the address into `subscribers.txt`
(one per line, `#` comments allowed) and it gets the next weekly email.

Everyone in that file is **BCC'd**, so no subscriber sees another's address;
`RECIPIENT_EMAIL` from `config.py` stays the visible `To:` and does not need a
line of its own. A line that doesn't look like an address is skipped with a
warning in `tea_tracker.log` rather than failing the run, and the file is
gitignored - it holds other people's addresses, so keep it off any public repo.
To remove someone, delete or comment out their line.

## What gets published, and why it isn't `tea_prices.db`

`tea_prices.db` is built for the scraper: it is indexed, it keeps three runs,
and it carries the raw product type and tags every classification decision was
made from, so a bad call can be traced back. The dashboard needs none of that,
and it is a web page that downloads the whole file before it can draw
anything - so every byte in it is a byte of someone's page load.

`tea_db.write_dashboard_copy()` therefore builds a separate copy for
publishing, with the ballast removed:

- **the four indexes** (31 of 84 MB), which sql.js never uses - it reads the
  one table start to finish;
- **six columns the dashboard never reads** (another 26 MB): `listing_key`,
  `site_tags`, `form_factor_description`, `product_handle`,
  `site_product_type` and the autoincrement `id`;
- **the third run.** The dashboard shows the newest and diffs it against the
  one before for "See what's new"; a third is never looked at.

Then VACUUM, then gzip: SQLite text compresses to about a fifth. In practice
**84 MB becomes about 3.5 MB**, and both the plain and the `.gz` copy are
published in the same commit. The page asks for the `.gz` first and unpacks it
with `DecompressionStream`, falling back to the plain file on a browser that
doesn't have one. Your local `tea_prices.db` keeps everything.

The page also lets the browser cache the download now. It used to pass
`cache: 'no-store'`, which forced a fresh copy of the whole database on every
single page load; GitHub Pages sends an ETag and a ten-minute max-age, so a
reload is now instant or a 304. The one cost is that a database pushed in the
last ten minutes can take one extra reload to appear - the scraper runs weekly.

## Data retention

`tea_prices.db` is intentionally kept small: every run trims anything older
than the 2 most recent prior sessions before adding its own, so the database
holds about 3 weeks of history at a time (see `tea_db.trim_old_sessions()`),
which keeps it cheap to commit weekly. **The CSVs in `output/` are never
trimmed** - they're your real, permanent history. For a full, untrimmed
database, run `migrate_csvs_to_db.py` against a separate `.db` path rather
than the live `tea_prices.db`.

## Security

- `config.py` contains a live credential. Add it to `.gitignore` (see the
  one in this folder) in **every** repo it could end up in, and never email,
  upload, or screenshot it.
- If this app password is ever exposed, revoke it immediately at
  myaccount.google.com and generate a new one.
- The dashboard repo/Pages site is public by default. `tea_prices.db` isn't
  especially sensitive, but anyone who finds the URL can see it - make the
  repo private (GitHub Pages supports that on paid plans) if that matters.

## Local testing of the dashboard

The auto-load uses `fetch()`, which browsers block on `file://` URLs for
security reasons. Double-clicking `index.html` will NOT auto-load a nearby
`tea_prices.db` - use the manual "Load Database" button, or serve locally:

```
python -m http.server 8000
```

then open `http://localhost:8000/` in a browser - `index.html` is served
at the directory root, so no filename is needed.
