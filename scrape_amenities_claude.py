"""
Claude-powered amenities/details scraper -- TEST RUN for Christchurch.

Fetches each clinic's website (homepage + about/team/faq/contact-style
subpages), asks Claude Haiku to extract a fixed set of "soft" fields
(parking, accessibility, sedation options, practitioner bios, etc.) that
aren't covered by the existing price scraper, and saves results to a local
JSON file for review.

This is a calibration run -- there is no Supabase table for this data yet,
so nothing is written to the database. Output: amenities_test_christchurch.json

Usage:
    python scrape_amenities_claude.py                  # all clinics in the input list
    python scrape_amenities_claude.py --limit 10        # first 10 only
"""

import json
import os
import re
import sys
import time
import requests
import anthropic
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DentalDirectoryBot/1.0)",
}

TIMEOUT = 12
MAX_TEXT_CHARS = 24000
MAX_PAGES = 10

INPUT_FILE = os.environ.get("AMENITIES_INPUT_FILE", "christchurch_clinics_for_amenities_test.json")
OUTPUT_FILE = os.environ.get("AMENITIES_OUTPUT_FILE", "amenities_test_christchurch.json")

# Broader than the price scraper's keyword list -- amenities/team info lives
# on About, Team, FAQ, and Contact pages, not just pricing pages.
PAGE_URL_KEYWORDS = {
    "about", "team", "staff", "dentist", "dentists", "meet", "our-team",
    "faq", "faqs", "contact", "location", "accessibility", "parking",
    "new-patient", "new-patients", "sedation", "technology", "story",
    "history", "why-us", "patients", "services",
}

SCHEMA = {
    "parking_access": None,
    "wheelchair_accessible": None,
    "same_day_emergency": None,
    "saturday_evening_hours": None,
    "practitioners": [],
    "in_house_specialists": None,
    "practice_size": None,
    "sedation_options": None,
    "calming_amenities": None,
    "dental_anxiety_friendly": None,
    "years_open": None,
    "awards": None,
    "professional_memberships": None,
    "before_after_gallery": None,
    "online_booking": None,
    "new_patient_forms_online": None,
    "payment_partners": None,
    "membership_plans": None,
    "kids_family_friendly": None,
}

PRACTITIONER_SCHEMA_NOTE = (
    '"practitioners" is a list of objects, one per dentist named on the site: '
    '{"name": str, "photo_url": str or null, "experience": str or null, '
    '"specialties": str or null, "bio": str or null, "languages": str or null}. '
    "Only include practitioners actually named on the page -- do not invent entries."
)


def safe(s: str) -> str:
    return s.encode("ascii", "replace").decode()


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lstrip("www.") or url
    except Exception:
        return url


def _fetch_soup(url: str):
    try:
        r = requests.get(url, headers=FETCH_HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code != 200:
            return None, None
        return r.url, BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None, None


def _soup_to_text(soup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)


def _extract_photo_urls(soup, base_url) -> list[str]:
    """Grab a handful of likely headshot image URLs (heuristic, best-effort)."""
    urls = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        alt = (img.get("alt") or "").lower()
        if any(kw in (src.lower() + alt) for kw in ("team", "dr-", "dr_", "doctor", "dentist", "staff", "headshot")):
            urls.append(urljoin(base_url, src))
    return urls[:20]


def _score_url(path: str) -> int:
    path_lower = path.lower()
    return sum(1 for kw in PAGE_URL_KEYWORDS if kw in path_lower)


def get_site_text(url: str) -> tuple[str | None, list[str]]:
    """Fetch homepage + prioritised subpages. Returns (combined_text, photo_urls)."""
    base_domain = urlparse(url).netloc
    visited = set()
    pages = []
    photo_urls = []

    final_url, soup = _fetch_soup(url)
    if soup is None:
        return None, []
    visited.add(final_url or url)
    pages.append((final_url or url, _soup_to_text(soup)))
    photo_urls.extend(_extract_photo_urls(soup, final_url or url))

    candidates = []
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"]).split("#")[0].split("?")[0]
        parsed = urlparse(href)
        if parsed.netloc != base_domain:
            continue
        if href in visited:
            continue
        if parsed.path.lower().endswith((".pdf", ".jpg", ".png", ".jpeg", ".gif")):
            continue
        score = _score_url(parsed.path)
        candidates.append((score, href))

    candidates.sort(key=lambda x: (-x[0], x[1]))
    seen_hrefs = set()
    queue = []
    for score, href in candidates:
        if href not in seen_hrefs:
            seen_hrefs.add(href)
            queue.append(href)

    for href in queue:
        if len(pages) >= MAX_PAGES:
            break
        if href in visited:
            continue
        visited.add(href)
        _, sub_soup = _fetch_soup(href)
        if sub_soup is None:
            continue
        pages.append((href, _soup_to_text(sub_soup)))
        photo_urls.extend(_extract_photo_urls(sub_soup, href))
        time.sleep(0.3)

    parts = []
    total = 0
    for page_url, text in pages:
        header = f"[Page: {page_url}]\n"
        available = MAX_TEXT_CHARS - total - len(header)
        if available <= 100:
            break
        chunk = text[:available]
        parts.append(header + chunk)
        total += len(header) + len(chunk)

    return ("\n\n".join(parts) if parts else None), photo_urls[:20]


# NOTE: output_config.format (structured outputs) was tried here but isn't a
# good fit for this schema -- ~20 properties plus a nested practitioners array
# either blows the union-type limit (when fields are nullable) or times out
# grammar compilation (even with single-typed fields). Sticking with prose
# JSON + a parse-retry loop instead, which is what the price scraper already
# uses successfully across 1300+ clinics.

AWARDS_NOTE = (
    '"awards": competitive prizes, medals, or "Best of ___" recognitions only -- '
    "things won or awarded, not memberships. Do NOT use star ratings or review "
    'counts (e.g. "4.9 stars") as an award. "professional_memberships": membership '
    "or fellowship of professional/specialist bodies (e.g. NZDA, RACDS, ICOI, NZ "
    "Academy of Cosmetic Dentistry, Royal College of Surgeons) -- voluntary but "
    "not competitive wins, keep separate from awards. Both are lists of strings."
)


def _build_prompt(clinic_name: str, url: str, text: str, photo_urls: list[str]) -> str:
    return f"""Extract practice-detail information from this dental clinic website. Only include information explicitly stated on the page -- do not infer, estimate, or fabricate anything. If something isn't mentioned, leave it null.

Clinic: {clinic_name}
URL: {url}

Candidate staff/team photo URLs found on the site (use these for practitioners.photo_url if you can match them to a named person, otherwise leave photo_url null):
{json.dumps(photo_urls[:20])}

Page text:
{text[:MAX_TEXT_CHARS]}

Fill in the JSON schema below. {PRACTITIONER_SCHEMA_NOTE}
- "parking_access": describe parking (car/bike) and wheelchair/step-free access if mentioned, as plain text. Set "wheelchair_accessible" separately to true/false/null based on explicit statements only.
- "sedation_options" and "calming_amenities" are different: sedation_options = clinical options (IV sedation, nitrous oxide, oral sedation); calming_amenities = non-clinical comfort features (TVs, headphones, music, blankets).
- "online_booking", "new_patient_forms_online", "wheelchair_accessible", "same_day_emergency", "saturday_evening_hours", "dental_anxiety_friendly", "before_after_gallery": true, false, or null -- never a string.
- {AWARDS_NOTE}
- All other fields are short plain-text strings or null.
- Escape any double-quote characters that appear inside string values (e.g. a quoted testimonial) so the JSON stays valid.

{json.dumps({**SCHEMA, "awards": [], "professional_memberships": []}, indent=2)}

Return ONLY valid JSON, no explanation or markdown."""


def ask_claude(clinic_name: str, url: str, text: str, photo_urls: list[str]) -> dict | None:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = _build_prompt(clinic_name, url, text, photo_urls)

    for attempt in range(2):
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            return json.loads(raw)
        except json.JSONDecodeError as e:
            if attempt == 0:
                print(f"    JSON parse failed, retrying once ({e})")
                continue
            print(f"    Claude error (after retry): {e}")
            return None
        except Exception as e:
            print(f"    Claude error: {e}")
            return None


def main():
    args = sys.argv[1:]
    limit = None
    for j, a in enumerate(args):
        if a == "--limit" and j + 1 < len(args):
            limit = int(args[j + 1])

    with open(INPUT_FILE, encoding="utf-8") as f:
        clinics = json.load(f)
    if limit:
        clinics = clinics[:limit]

    print(f"Amenities scraper (TEST) -- {len(clinics)} Christchurch clinics\n")

    results = []
    errors = 0

    for i, clinic in enumerate(clinics, 1):
        cid = clinic["id"]
        name = safe(clinic["name"])
        url = clinic["website"]

        text, photo_urls = get_site_text(url)
        if text is None:
            print(f"  [{i:3d}/{len(clinics)}] ERR  {name} (site unreachable)")
            errors += 1
            results.append({"id": cid, "name": clinic["name"], "url": url, "error": "Website could not be fetched"})
            continue

        data = ask_claude(clinic["name"], url, text, photo_urls)
        if data is None:
            print(f"  [{i:3d}/{len(clinics)}] ERR  {name} (Claude failed)")
            errors += 1
            results.append({"id": cid, "name": clinic["name"], "url": url, "error": "Claude API error"})
            continue

        filled = sum(1 for k, v in data.items() if v not in (None, [], ""))
        print(f"  [{i:3d}/{len(clinics)}] {name} -- {filled}/{len(SCHEMA)} fields filled")

        results.append({"id": cid, "name": clinic["name"], "url": url, "data": data})
        time.sleep(0.5)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Scanned: {len(clinics)}, Errors: {errors}")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
