# Daily job scan (Amsterdam, English)

Runs on GitHub Actions every day. Sources: JobSpy (Indeed, Glassdoor, Google Jobs) and an Apify Indeed actor.
LinkedIn is not scraped and no personal account or cookie is used anywhere.

## Setup (once)
1. Create a **public** GitHub repo (it only stores public job listings, no personal data) and push these files.
2. Repo > Settings > Secrets and variables > Actions > New repository secret: `APIFY_TOKEN` = your Apify API token (Apify Console > Settings > Integrations).
3. Repo > Actions > "Daily job scan" > Run workflow to test.
4. Results appear in `data/latest.csv` (`is_new` marks listings not seen before).

## Tuning
Edit `QUERIES`, `EXCLUDE_TITLE` (sales/BD/senior are dropped) and `HOURS_OLD` in `scan.py`.
If Indeed starts blocking GitHub IPs, add a proxy via the `proxies=` argument or rely on the Apify source.
