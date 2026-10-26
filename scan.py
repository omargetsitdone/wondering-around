"""Daily Amsterdam job scan: JobSpy (Glassdoor, Google Jobs).

Indeed and LinkedIn are NOT scraped here: they run through Apify from the Claude scheduled task.

LinkedIn is deliberately excluded. Output: data/latest.csv (rolling file, newest first)
and data/seen.json (dedupe memory). Excludes sales / business-development titles.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from jobspy import scrape_jobs

DATA = Path("data")
DATA.mkdir(exist_ok=True)
SEEN_FILE = DATA / "seen.json"
LATEST = DATA / "latest.csv"

LOCATION = "Amsterdam, Netherlands"
RESULTS_PER_QUERY = 25
HOURS_OLD = 72

# Track A: trading / commodities support (no sales / BD)
# Track B: international B2B / product marketing
# Track C: junior public-sector / policy / research
QUERIES = {
    "A": ["trade support analyst", "trading analyst junior", "commodities analyst junior",
          "trade operations", "freight chartering coordinator", "market analyst junior"],
    "B": ["junior marketing specialist B2B", "product marketing junior", "marketing coordinator international"],
    "C": ["junior policy advisor", "policy analyst junior", "research assistant economics",
          "regulatory affairs junior", "public affairs junior", "economist junior"],
}

# Drop sales / BD roles (user excluded them), and clearly senior roles.
EXCLUDE_TITLE = re.compile(
    r"\b(sales|business development|account (manager|executive)|bdm|sdr|bdr|"
    r"senior|sr\.?|lead|head of|director|principal|manager)\b", re.I)
DUTCH_REQUIRED = re.compile(
    r"(vloeiend nederlands|dutch (is )?(required|mandatory|fluent)|fluent in dutch|"
    r"native dutch|nederlands (als moedertaal|vereist)|excellent .{0,20}dutch)", re.I)


def run_jobspy() -> pd.DataFrame:
    frames = []
    for track, terms in QUERIES.items():
        for term in terms:
            try:
                df = scrape_jobs(
                    # No linkedin (excluded by user) and no indeed (handled by Apify).
                    # zip_recruiter is US/CA-only; bayt/naukri/bdjobs/hellowork don't serve Amsterdam.
                    site_name=["glassdoor", "google"],
                    search_term=term,
                    google_search_term=f"{term} jobs in Amsterdam since last week",
                    location=LOCATION,
                    distance=15,
                    results_wanted=RESULTS_PER_QUERY,
                    hours_old=HOURS_OLD,
                    country_indeed="netherlands",
                    description_format="markdown",
                    verbose=0,
                )
            except Exception as exc:  # one failing site/query must not kill the run
                print(f"[jobspy] {term!r} failed: {exc}", file=sys.stderr)
                continue
            if df is None or df.empty:
                continue
            df["track"] = track
            df["query"] = term
            df["source"] = "jobspy:" + df["site"].astype(str)
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def normalise(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    for col in ["title", "company", "location", "job_url", "description", "date_posted"]:
        if col not in df:
            df[col] = ""
    df["description"] = df["description"].fillna("").astype(str)
    df["title"] = df["title"].fillna("").astype(str)
    df = df[df["job_url"].notna() & (df["job_url"] != "")]
    df = df[~df["title"].str.contains(EXCLUDE_TITLE)]
    df = df[df["location"].fillna("").str.contains("Amsterdam|Amstelveen|Schiphol|Zuidas|Netherlands|Remote", case=False)]
    df["dutch_required"] = df["description"].str.contains(DUTCH_REQUIRED)
    df["english_ad"] = ~df["description"].str.contains(
        r"\b(wij zoeken|jouw taken|wat ga je doen|wat bieden wij|solliciteer)\b", case=False)
    df["key"] = (df["company"].fillna("").str.lower().str.strip() + "|" +
                 df["title"].str.lower().str.strip())
    return df.drop_duplicates("key")


def main() -> None:
    seen = set(json.loads(SEEN_FILE.read_text())) if SEEN_FILE.exists() else set()
    df = normalise(run_jobspy())
    if df.empty:
        print("No results this run.")
        return
    df["is_new"] = ~df["key"].isin(seen)
    df["scanned_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    keep = ["is_new", "scanned_at", "track", "title", "company", "location", "job_type",
            "date_posted", "dutch_required", "english_ad", "source", "job_url", "job_url_direct",
            "min_amount", "max_amount", "salary", "description"]
    out = df[[c for c in keep if c in df.columns]].copy()
    out["description"] = out["description"].str.slice(0, 1500)
    out.to_csv(LATEST, index=False)
    SEEN_FILE.write_text(json.dumps(sorted(seen | set(df["key"]))))
    print(f"{len(out)} listings, {int(out['is_new'].sum())} new")


if __name__ == "__main__":
    main()
