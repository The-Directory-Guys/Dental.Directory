"""
Keyword scan + Claude pass for new-patient acceptance status.

Pass 1 (default): keyword scan only — writes clear yes/no to Supabase.
Pass 2 (--pass2):  re-scans null clinics, calls Claude on ambiguous pages.

Usage:
    python scrape_new_patients.py           # Pass 1 preview
    python scrape_new_patients.py --apply   # Pass 1 apply
    python scrape_new_patients.py --pass2           # Pass 2 preview
    python scrape_new_patients.py --pass2 --apply   # Pass 2 apply
"""

import os
import re
import sys
import time
import anthropic
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DentalDirectoryBot/1.0)",
}

TIMEOUT = 10

YES_PATTERNS = re.compile(
    r"\b(now\s+)?accepting\s+new\s+patients"
    r"|\bwelcoming\s+new\s+patients"
    r"|\bnew\s+patients\s+(are\s+)?welcome"
    r"|\bwe\s+welcome\s+new\s+patients"
    r"|\bopen\s+to\s+new\s+patients"
    r"|\bbooks?\s+are\s+(now\s+)?open"
    r"|\btaking\s+on\s+new\s+patients"
    r"|\bnew\s+patient\s+(appointments?|bookings?|enquiries)\s+welcome"
    r"|\bregister\s+as\s+a\s+new\s+patient"
    r"|\bnew\s+patients\s+can\s+book"
    r"|\bbecome\s+a\s+(new\s+)?patient",
    re.IGNORECASE,
)

NO_PATTERNS = re.compile(
    r"\bnot\s+(currently\s+)?accepting\s+new\s+patients"
    r"|\bno\s+longer\s+accepting\s+new\s+patients"
    r"|\bnot\s+taking\s+(on\s+)?new\s+patients"
    r"|\bnot\s+(currently\s+)?taking\s+new\s+patients"
    r"|\bbooks?\s+are\s+(currently\s+)?(closed|full)"
    r"|\bour\s+books?\s+(are\s+)?(closed|full)"
    r"|\bclosed\s+to\s+new\s+patients"
    r"|\bunable\s+to\s+accept\s+new\s+patients"
    r"|\bno\s+new\s+patients",
    re.IGNORECASE,
)

ANY_PATTERN = re.compile(r"\bnew\s+patients?\b", re.IGNORECASE)

MAX_TEXT_CHARS = 8000  # truncate before sending to Claude


def fetch_clinics(null_only: bool) -> list[dict]:
    all_rows = []
    page_size = 1000
    offset = 0
    null_filter = "&open_to_new_patients=is.null" if null_only else ""
    while True:
        url = (
            f"{SUPABASE_URL}/rest/v1/dental_clinics"
            f"?select=id,name,website"
            f"&website=not.is.null&website=neq."
            f"{null_filter}"
            f"&order=id.asc"
            f"&limit={page_size}&offset={offset}"
        )
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        rows = r.json()
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        offset += page_size
    return all_rows


def get_page_text(url: str) -> str | None:
    try:
        r = requests.get(url, headers=FETCH_HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return soup.get_text(" ", strip=True)
    except Exception:
        return None


def classify(text: str) -> str:
    """Return 'yes', 'no', 'ambiguous', or 'none'."""
    if NO_PATTERNS.search(text):
        return "no"
    if YES_PATTERNS.search(text):
        return "yes"
    if ANY_PATTERN.search(text):
        return "ambiguous"
    return "none"


def ask_claude(clinic_name: str, text: str) -> bool | None:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are reviewing a dental clinic website to determine whether the clinic is currently accepting new patients.

Clinic: {clinic_name}

Website text (truncated):
{text[:MAX_TEXT_CHARS]}

Based only on what is written above, is this clinic currently accepting new patients?
Reply with exactly one word: YES, NO, or UNKNOWN."""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = msg.content[0].text.strip().upper()
    if answer == "YES":
        return True
    if answer == "NO":
        return False
    return None


def update_clinic(clinic_id: int, value: bool):
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/dental_clinics?id=eq.{clinic_id}",
        headers=HEADERS,
        json={"open_to_new_patients": value},
        timeout=15,
    )
    r.raise_for_status()


def safe(s: str) -> str:
    return s.encode("ascii", "replace").decode()


# ---------------------------------------------------------------------------
# Pass 1
# ---------------------------------------------------------------------------

def run_pass1(apply: bool):
    print(f"Pass 1 — keyword scan ({'APPLY' if apply else 'PREVIEW'})")
    print("Fetching clinic list...")
    clinics = fetch_clinics(null_only=False)
    print(f"  {len(clinics)} clinics to scan\n")

    results = {"yes": [], "no": [], "ambiguous": [], "none": [], "error": []}

    for i, clinic in enumerate(clinics, 1):
        name = safe(clinic["name"])
        website = clinic["website"]
        cid = clinic["id"]

        text = get_page_text(website)
        if text is None:
            results["error"].append((name, website))
            print(f"  [{i:4d}/{len(clinics)}] ERR  {name}")
            continue

        result = classify(text)
        results[result].append((cid, name, website))
        label = {"yes": "YES ", "no": "NO  ", "ambiguous": "AMB ", "none": "----"}[result]
        print(f"  [{i:4d}/{len(clinics)}] {label} {name}")

        if apply and result in ("yes", "no"):
            update_clinic(cid, result == "yes")

        time.sleep(0.3)

    print(f"\n{'='*60}")
    print(f"Results ({len(clinics)} scanned):")
    print(f"  Accepting new patients:     {len(results['yes'])}")
    print(f"  NOT accepting new patients: {len(results['no'])}")
    print(f"  Ambiguous (needs Claude):   {len(results['ambiguous'])}")
    print(f"  No mention:                 {len(results['none'])}")
    print(f"  Fetch errors:               {len(results['error'])}")

    if results["ambiguous"]:
        print(f"\nAmbiguous clinics (Pass 2 candidates):")
        for _, name, url in results["ambiguous"]:
            print(f"  {name} - {url}")

    if not apply:
        print("\nRun with --apply to write yes/no results to Supabase.")


# ---------------------------------------------------------------------------
# Pass 2
# ---------------------------------------------------------------------------

def run_pass2(apply: bool):
    print(f"Pass 2 — Claude on ambiguous pages ({'APPLY' if apply else 'PREVIEW'})")
    print("Fetching null clinics...")
    clinics = fetch_clinics(null_only=True)
    print(f"  {len(clinics)} clinics with open_to_new_patients = null\n")

    counts = {"true": 0, "false": 0, "unknown": 0, "no_mention": 0, "error": 0}

    for i, clinic in enumerate(clinics, 1):
        name = safe(clinic["name"])
        website = clinic["website"]
        cid = clinic["id"]

        text = get_page_text(website)
        if text is None:
            counts["error"] += 1
            print(f"  [{i:4d}/{len(clinics)}] ERR  {name}")
            continue

        if not ANY_PATTERN.search(text):
            counts["no_mention"] += 1
            print(f"  [{i:4d}/{len(clinics)}] ---- {name}  (no mention)")
            continue

        # Ambiguous — ask Claude
        result = ask_claude(clinic["name"], text)
        if result is True:
            counts["true"] += 1
            label = "YES "
        elif result is False:
            counts["false"] += 1
            label = "NO  "
        else:
            counts["unknown"] += 1
            label = "UNK "

        print(f"  [{i:4d}/{len(clinics)}] {label} {name}")

        if apply and result is not None:
            update_clinic(cid, result)

        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"Pass 2 results ({len(clinics)} null clinics):")
    print(f"  Accepting (Claude YES):     {counts['true']}")
    print(f"  Not accepting (Claude NO):  {counts['false']}")
    print(f"  Unknown (Claude uncertain): {counts['unknown']}")
    print(f"  No mention (skipped):       {counts['no_mention']}")
    print(f"  Fetch errors:               {counts['error']}")

    if not apply:
        print("\nRun with --apply to write results to Supabase.")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    apply = "--apply" in sys.argv
    if "--pass2" in sys.argv:
        run_pass2(apply)
    else:
        run_pass1(apply)
