#!/usr/bin/env python3
"""
Best-effort price extraction from clinic websites for one region (CSV).

Fetches each practice homepage, follows same-domain links that look like
fees/pricing pages, then extracts NZD amounts with regex. Many sites do not
publish prices. Generic Lumino practice pages are skipped except Greymouth
Family Dental and Garry Rae Greymouth, which are given the national $99
new-patient offer (see lumino_greymouth_99_offer).

Usage:
  python scrape_region_prices.py --region "West Coast"
  python scrape_region_prices.py --region "West Coast" --json-out west_coast_prices.json
  python scrape_region_prices.py --region "West Coast" --push-supabase

Requires: requests, beautifulsoup4. Optional: SUPABASE_URL + SUPABASE_SERVICE_KEY in .env
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SOURCE_PREFIX = "region_website_scrape"
SOURCE_LUMINO_99 = "lumino_new_patient_99"

# Google Maps URL cid fragments — Greymouth Lumino practices on $99 new patient national offer
LUMINO_99_GREYMOUTH_CID = (
    "cid=12335065779227543131",  # Greymouth Family Dental Centre
    "cid=15764414591835748325",  # Garry Rae Dental Greymouth
)
LUMINO_99_OFFER_PAGE = "https://lumino.co.nz/pricing-offers/99-new-patient-check-up/"


def lumino_greymouth_99_offer(gmaps_url: str) -> list[dict[str, Any]] | None:
    if not gmaps_url or not any(m in gmaps_url for m in LUMINO_99_GREYMOUTH_CID):
        return None
    return [
        {
            "treatment": "New patient exam and x-rays (promotional offer)",
            "price_nzd": 99,
            "price_label": "$99 New Patient Check-Up (Lumino national offer)",
            "source_url": LUMINO_99_OFFER_PAGE,
            "notes": "Participating Lumino practice; confirm availability and terms when booking.",
        }
    ]


USER_AGENT = (
    "Mozilla/5.0 (compatible; DentalDirectoryBot/1.0; +https://example.org)"
)


def load_env_from_dotenv() -> None:
    root = Path(__file__).resolve().parent
    for name in (".env", ".env.txt"):
        path = root / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            t = line.strip()
            if not t or t.startswith("#") or "=" not in t:
                continue
            key, _, val = t.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
        break


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    return s


def looks_like_clinic_website(url: str) -> bool:
    """
    Best-effort guard against obvious non-clinic sites accidentally present in the CSV.
    We only use this to *skip* clearly-wrong domains/paths (e.g. history sites).
    """
    if not url:
        return False
    try:
        u = urlparse(url)
    except OSError:
        return False
    host = (u.netloc or "").lower()
    path = (u.path or "").lower()
    if not host:
        return False

    blocked_hosts = {
        "nzhistory.govt.nz",
        "en.wikipedia.org",
        "www.wikipedia.org",
        "teara.govt.nz",
        "natlib.govt.nz",
        "www.doc.govt.nz",
        "www.newzealand.com",
    }
    if host in blocked_hosts:
        return False
    if "church" in path and "dental" not in path and "dent" not in path:
        return False
    return True


def looks_like_dental_homepage(url: str, text: str, *, redirected_from: str | None = None) -> bool:
    """
    Best-effort guard against listings that aren't dental clinics but slipped into the CSV.
    This is intentionally conservative: only skip when the homepage *really* doesn't look dental.
    """
    host = ""
    try:
        host = (urlparse(url).netloc or "").lower()
    except OSError:
        host = ""

    dentalish_host = any(k in host for k in ("dental", "dentist", "orthodont", "oral", "denture"))
    # If the domain itself screams "dental", trust it.
    if dentalish_host:
        return True

    t = (text or "").lower()
    # Remove some noise from the check.
    t = re.sub(r"\s+", " ", t)

    positive = (
        "dental",
        "dentist",
        "dentistry",
        "orthodont",
        "hygienist",
        "tooth",
        "teeth",
        "oral health",
        "root canal",
        "filling",
        "crown",
        "dentures",
        "check-up",
        "x-ray",
    )
    has_positive = any(p in t for p in positive)
    if has_positive:
        return True

    # Strong negative signals for false listings.
    negative = (
        "church",
        "cathedral",
        "museum",
        "war memorial",
        "history",
        "heritage",
        "tourism",
        "book a tour",
        "exhibition",
    )
    if any(n in t for n in negative):
        return False

    # If we were redirected to a different domain, be stricter: require positive signals.
    if redirected_from:
        try:
            from_host = (urlparse(redirected_from).netloc or "").lower()
        except OSError:
            from_host = ""
        if from_host and from_host != host:
            return False

    # Otherwise, be conservative (don't skip), since some clinic sites are image-heavy.
    return True


def _same_domain(base: str, url: str) -> bool:
    try:
        return urlparse(base).netloc.lower() == urlparse(url).netloc.lower()
    except OSError:
        return False


def _looks_like_price_page(link_text: str, href: str) -> bool:
    h = (link_text or "") + " " + (href or "")
    p = (urlparse(href).path or "").lower()
    return bool(
        re.search(
            r"fee|price|cost|payment|invest|plan|offer|promo|finance",
            h + " " + p,
            re.I,
        )
    )


def extract_dollar_amounts(text: str) -> list[dict[str, Any]]:
    """Return unique dollar amounts with short context snippets."""
    found: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()

    def clean_snippet(s: str) -> str:
        s = re.sub(r"[^\x20-\x7E]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    for m in re.finditer(r"\$\s*([\d,]+(?:\.\d{1,2})?)", text):
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        amt = int(round(val))
        if amt < 5 or amt > 25000:
            continue
        if re.search(r"20\d{2}", text[max(0, m.start() - 4) : m.end() + 4]):
            # Likely a year near $ — skip
            continue
        snippet = text[max(0, m.start() - 60) : m.end() + 80]
        snippet = clean_snippet(snippet)
        key = (amt, snippet[:80])
        if key in seen:
            continue
        seen.add(key)
        found.append({"price_nzd": amt, "context": snippet[:400]})
    return found[:25]


def scrape_clinic_website(start_url: str) -> tuple[list[dict[str, Any]], list[str], str | None]:
    """
    Returns (rows for scraped_prices, source_urls_used, error_message).
    Each row: treatment, price_nzd, price_label, source_url, notes
    """
    session = _session()
    source_urls: list[str] = []
    try:
        r = session.get(start_url, timeout=25, allow_redirects=True)
        r.raise_for_status()
    except OSError as e:
        return [], [], str(e)

    final = r.url
    source_urls.append(final)
    blobs: list[str] = []

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    homepage_text = soup.get_text(" ", strip=True)
    if not looks_like_dental_homepage(final, homepage_text, redirected_from=start_url):
        return [], [final], "Homepage does not look like a dental clinic; skipping"
    blobs.append(homepage_text)

    candidates: list[str] = []
    seen: set[str] = {final}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full = urljoin(final, href)
        if not _same_domain(final, full):
            continue
        if full in seen:
            continue
        if _looks_like_price_page(a.get_text(" ", strip=True), href):
            candidates.append(full)

    for u in dict.fromkeys(candidates):
        if len(source_urls) >= 8:
            break
        try:
            r2 = session.get(u, timeout=18, allow_redirects=True)
            if not r2.ok:
                continue
            seen.add(r2.url)
            source_urls.append(r2.url)
            s2 = BeautifulSoup(r2.text, "html.parser")
            for tag in s2(["script", "style", "noscript"]):
                tag.decompose()
            blobs.append(s2.get_text(" ", strip=True))
        except OSError:
            continue

    blob = " ".join(blobs)
    amounts = extract_dollar_amounts(blob)
    rows: list[dict[str, Any]] = []
    for i, a in enumerate(amounts):
        rows.append(
            {
                "treatment": f"Heuristic scrape #{i + 1} (verify on site)",
                "price_nzd": a["price_nzd"],
                "price_label": a["context"][:160],
                "source_url": source_urls[0],
                "notes": f"Context: {a['context'][:500]}",
            }
        )
    return rows, source_urls, None


def merge_heuristic_scrapes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Collapse multiple regex hits for one clinic into a single row for storage."""
    if not rows:
        raise ValueError("merge_heuristic_scrapes requires at least one row")
    if len(rows) == 1:
        # Still include a consistent disclaimer for heuristic rows.
        r0 = rows[0]
        base_notes = (r0.get("notes") or "").strip()
        disclaimer = (
            "Disclaimer: Costs published are estimates only. You should be provided with a treatment plan "
            "and advised of any proposed changes during the course of treatment."
        )
        notes = f"{base_notes}\n\n{disclaimer}".strip() if base_notes else disclaimer
        return {**r0, "notes": notes}
    primary = rows[0]

    def service_hint(text: str) -> str | None:
        t = (text or "").lower()
        if "routine exam" in t or "routine exams" in t:
            return "Routine exam"
        if "dental hygienist" in t or "hygien" in t:
            return "Dental hygienist"
        if "x-ray" in t or "xray" in t:
            return "X-ray"
        return None

    summary_parts: list[str] = []
    for r in rows:
        hint = service_hint((r.get("notes") or "") + " " + (r.get("price_label") or ""))
        if hint:
            summary_parts.append(f"{hint} from ${r['price_nzd']}")
        else:
            summary_parts.append(f"From ${r['price_nzd']}")
    summary = "; ".join(dict.fromkeys(summary_parts))

    disclaimer = (
        "Disclaimer: Costs published are estimates only. You should be provided with a treatment plan "
        "and advised of any proposed changes during the course of treatment."
    )
    merged_notes = f"{disclaimer}\n\nServices/amounts seen: {summary}".strip()
    return {
        "treatment": "Heuristic scrape (verify on site)",
        "price_nzd": primary["price_nzd"],
        "price_label": summary[:160] if summary else primary["price_label"],
        "source_url": primary["source_url"],
        "notes": merged_notes,
    }


def load_region_rows(csv_path: Path, region: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with csv_path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("region") or "").strip() == region:
                rows.append(row)
    return rows


def fetch_clinic_ids_by_url(
    supabase_url: str, service_key: str, region: str
) -> dict[str, int]:
    """Map google_maps_url -> dental_clinics.id for the region."""
    base = supabase_url.rstrip("/")
    endpoint = f"{base}/rest/v1/dental_clinics"
    params = {
        "select": "id,google_maps_url",
        "region": f"eq.{region}",
    }
    r = requests.get(
        endpoint,
        params=params,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    out: dict[str, int] = {}
    for row in data:
        u = (row.get("google_maps_url") or "").strip()
        if u:
            out[u] = int(row["id"])
    return out


def push_rows(
    supabase_url: str,
    service_key: str,
    rows: list[dict[str, Any]],
) -> None:
    if not rows:
        print("Nothing to push.", file=sys.stderr)
        return
    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/scraped_prices"
    now = datetime.now(timezone.utc).isoformat()
    payload = [
        {
            "clinic_id": r["clinic_id"],
            "source": r["source"],
            "treatment": r["treatment"],
            "price_nzd": r["price_nzd"],
            "price_label": r["price_label"],
            "source_url": r["source_url"],
            "notes": r.get("notes"),
            "scraped_at": now,
        }
        for r in rows
    ]
    r = requests.post(
        endpoint,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json=payload,
        timeout=120,
    )
    if not r.ok:
        print(r.text[:2500], file=sys.stderr)
        r.raise_for_status()
    print(f"Inserted {len(payload)} row(s) into scraped_prices.", file=sys.stderr)


def run_region(
    csv_path: Path,
    region: str,
) -> dict[str, Any]:
    source = f"{SOURCE_PREFIX}:{region}"
    out: dict[str, Any] = {
        "region": region,
        "source": source,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "clinics": [],
    }
    push_rows_flat: list[dict[str, Any]] = []

    id_by_url: dict[str, int] | None = None
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"):
        try:
            id_by_url = fetch_clinic_ids_by_url(
                os.environ["SUPABASE_URL"],
                os.environ["SUPABASE_SERVICE_KEY"],
                region,
            )
        except OSError as e:
            print("Warning: could not load clinic IDs from Supabase:", e, file=sys.stderr)

    for row in load_region_rows(csv_path, region):
        name = (row.get("name") or "").strip()
        website = (row.get("website") or "").strip()
        gmaps = (row.get("google_maps_url") or "").strip()

        entry: dict[str, Any] = {
            "name": name,
            "website": website,
            "google_maps_url": gmaps,
            "status": "pending",
            "scraped_rows": [],
            "detail": None,
        }

        if not website:
            entry["status"] = "no_website"
            entry["detail"] = "No website URL in CSV"
            out["clinics"].append(entry)
            continue

        if not looks_like_clinic_website(website):
            entry["status"] = "skipped_non_clinic_website"
            entry["detail"] = "Website URL looks unrelated to a dental clinic; skipping"
            out["clinics"].append(entry)
            continue

        if "lumino.co.nz" in website.lower():
            offer_99 = lumino_greymouth_99_offer(gmaps)
            if offer_99:
                entry["status"] = "ok"
                entry["detail"] = (
                    "Lumino $99 new patient offer (national promo; this practice participates)"
                )
                clinic_id = None
                if id_by_url and gmaps in id_by_url:
                    clinic_id = id_by_url[gmaps]
                for sr in offer_99:
                    sr_out = {**sr, "clinic_id": clinic_id, "source": SOURCE_LUMINO_99}
                    entry["scraped_rows"].append(sr_out)
                    push_rows_flat.append(
                        {
                            "clinic_id": clinic_id,
                            "source": SOURCE_LUMINO_99,
                            "treatment": f"{name}: {sr['treatment']}",
                            "price_nzd": sr["price_nzd"],
                            "price_label": sr["price_label"],
                            "source_url": sr["source_url"],
                            "notes": sr.get("notes"),
                        }
                    )
                out["clinics"].append(entry)
                continue
            entry["status"] = "lumino_skipped"
            entry["detail"] = "Lumino does not publish per-practice fee schedules online"
            out["clinics"].append(entry)
            continue

        scraped, urls, err = scrape_clinic_website(website)
        if err:
            entry["status"] = "fetch_error"
            entry["detail"] = err
            out["clinics"].append(entry)
            continue

        entry["pages_fetched"] = urls
        if not scraped:
            entry["status"] = "no_amounts_found"
            entry["detail"] = "No $ amounts found in homepage + fee-like linked pages"
        else:
            entry["status"] = "ok"

        clinic_id = None
        if id_by_url and gmaps in id_by_url:
            clinic_id = id_by_url[gmaps]

        if scraped:
            sr = merge_heuristic_scrapes(scraped)
            sr_out = {
                **sr,
                "clinic_id": clinic_id,
                "source": source,
            }
            entry["scraped_rows"].append(sr_out)
            push_rows_flat.append(
                {
                    "clinic_id": clinic_id,
                    "source": source,
                    "treatment": f"{name}: {sr['treatment']}",
                    "price_nzd": sr["price_nzd"],
                    "price_label": sr["price_label"],
                    "source_url": sr["source_url"],
                    "notes": sr.get("notes"),
                }
            )

        out["clinics"].append(entry)

    out["_push_preview_count"] = len(push_rows_flat)
    out["_push_rows"] = push_rows_flat
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Scrape heuristic prices from clinic websites by region")
    ap.add_argument("--region", default="West Coast", help="CSV region name (exact match)")
    ap.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).resolve().parent / "dental_clinics_all.csv",
        help="Path to dental_clinics_all.csv",
    )
    ap.add_argument("--json-out", type=Path, help="Write full JSON report")
    ap.add_argument("--push-supabase", action="store_true", help="Insert scraped rows (needs service key)")
    args = ap.parse_args()
    load_env_from_dotenv()

    if not args.csv.is_file():
        print("CSV not found:", args.csv, file=sys.stderr)
        sys.exit(1)

    report = run_region(args.csv, args.region)
    push_rows_data = report.pop("_push_rows", [])
    preview = report.pop("_push_preview_count", 0)

    # ASCII-safe for Windows consoles; use --json-out for UTF-8
    print(json.dumps(report, indent=2, ensure_ascii=True))

    if args.json_out:
        full = {**report, "_push_preview_count": preview, "_push_rows": push_rows_data}
        args.json_out.write_text(json.dumps(full, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.push_supabase:
        url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        if not url or not key:
            print("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY", file=sys.stderr)
            sys.exit(1)
        push_rows(url, key, push_rows_data)


if __name__ == "__main__":
    main()
