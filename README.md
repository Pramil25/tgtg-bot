# Fob Sushi Bellevue — TGTG Availability Notifier

Checks Too Good To Go every 5 minutes for Fob Sushi Bellevue bags and pushes
a phone notification the instant one is available, so you can jump into the
app and reserve it manually. Runs free on GitHub Actions — no server needed.

## 1. Get your phone ready for notifications (2 min)
1. Install the **ntfy** app: [iOS](https://apps.apple.com/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
2. In the app, subscribe to a topic name only you know, e.g. `pramil-tgtg-8f3k2`
   (topics are public by name, so pick something hard to guess — don't use
   just "sushi" or your name).

## 2. Get TGTG credentials (one-time, on your own computer)
```bash
pip install tgtg
python auth.py
```
- Enter your TGTG account email.
- Check your email/app for the TGTG login link and click it within ~1 minute.
- The script prints 4 values — copy them.

## 3. Put this code on GitHub
1. Create a new **public** repo (e.g. `tgtg-bot`). It needs to be public —
   GitHub's cron can't trigger more often than every 5 minutes, so this
   workflow instead loops internally every ~20 seconds for most of that
   5-minute window. That uses a lot of Actions minutes, which is free and
   unlimited on public repos but would blow through the 2,000 free
   minutes/month on a private repo in under a day. Your tokens stay safe
   as encrypted secrets regardless of repo visibility.
2. Push these files to it (`check_tgtg.py`, `.github/workflows/check.yml`).
3. Go to **Settings → Secrets and variables → Actions → New repository secret**
   and add each of these:
   - `TGTG_ACCESS_TOKEN`
   - `TGTG_REFRESH_TOKEN`
   - `TGTG_COOKIE`
   - `NTFY_TOPIC` — the topic name you picked in step 1

## 4. Done
GitHub will now run the check every 5 minutes automatically, for free, with
nothing running on your own machine. You can watch it work under the
**Actions** tab, or trigger it manually anytime with "Run workflow".

## How fast is "fast"?
Effectively ~20 seconds — each 5-minute-triggered run rechecks every 20s
for ~4m40s before handing off to the next trigger. If a bag disappears and
reappears later you'll get a fresh ping (dedupe only suppresses repeat
alerts while it stays continuously available).

## Notes / limits
- TGTG's tokens can expire after a few weeks of no use — if the job starts
  failing in the Actions log, just re-run `auth.py` and update the secrets.
- This uses an unofficial, reverse-engineered TGTG API via the community
  `tgtg` Python package (widely used for personal notification bots like
  this). It only *reads* availability and never places an order automatically —
  reserving the bag is still a manual tap on your end, which keeps you
  squarely on the right side of TGTG's terms.
- GitHub's free tier cron can occasionally run a few minutes late during
  high load — fine for this use case, but not millisecond-precise.
