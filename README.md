# Job scan (Amsterdam, English)

GitHub Action runs every 3 days: JobSpy over Glassdoor and Google Jobs. Results: `data/latest.csv`.
Indeed and LinkedIn are scraped through Apify (no login, no personal account) by the Claude scheduled task, not this repo.
No secrets are needed.

Run manually: Actions > "Job scan (JobSpy)" > Run workflow.
Tune `QUERIES`, `EXCLUDE_TITLE`, `HOURS_OLD` in `scan.py`.
