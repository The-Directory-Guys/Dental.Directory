"""
Geocode all dental clinics using Nominatim (OpenStreetMap).
Adds lat/lng to the dental_clinics table in Supabase.

Prerequisites:
  Run this SQL in Supabase dashboard first:
    ALTER TABLE dental_clinics ADD COLUMN IF NOT EXISTS lat DOUBLE PRECISION;
    ALTER TABLE dental_clinics ADD COLUMN IF NOT EXISTS lng DOUBLE PRECISION;

Usage:
  python supabase/geocode.py
"""

import urllib.request, urllib.parse, json, time, sys, os
sys.stdout.reconfigure(encoding="utf-8")

def load_env():
    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return
    for line in open(env_path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS_READ = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
}
HEADERS_WRITE = {**HEADERS_READ, "Content-Type": "application/json"}

def supabase_get(path):
    req = urllib.request.Request(f"{SUPABASE_URL}{path}", headers=HEADERS_READ)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def supabase_patch(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{SUPABASE_URL}{path}", data=data, headers=HEADERS_WRITE, method="PATCH"
    )
    with urllib.request.urlopen(req) as r:
        return r.status

def geocode(address):
    params = urllib.parse.urlencode({
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "nz",
    })
    req = urllib.request.Request(
        f"{NOMINATIM_URL}?{params}",
        headers={"User-Agent": "DentalCompareNZ/1.0 (chasesmith2040@gmail.com)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            results = json.loads(r.read())
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        print(f"  Nominatim error: {e}")
    return None, None

def main():
    # Fetch all clinics missing lat/lng
    print("Fetching clinics without coordinates...")
    PAGE = 1000
    clinics = []
    for offset in range(0, 9999, PAGE):
        page = supabase_get(
            f"/rest/v1/dental_clinics?select=id,name,address,suburb_town,region"
            f"&lat=is.null&business_status=eq.OPERATIONAL"
            f"&limit={PAGE}&offset={offset}"
        )
        clinics.extend(page)
        if len(page) < PAGE:
            break

    total = len(clinics)
    print(f"{total} clinics to geocode. Estimated time: ~{total // 60 + 1} min\n")

    ok = skip = fail = 0

    for i, clinic in enumerate(clinics, 1):
        address = clinic.get("address", "").strip()
        name = clinic["name"]

        if not address:
            print(f"[{i}/{total}] SKIP (no address): {name}")
            skip += 1
            time.sleep(1)
            continue

        lat, lng = geocode(address)

        if lat is not None:
            supabase_patch(
                f"/rest/v1/dental_clinics?id=eq.{clinic['id']}",
                {"lat": lat, "lng": lng},
            )
            print(f"[{i}/{total}] OK  {name} → {lat:.5f}, {lng:.5f}")
            ok += 1
        else:
            # Retry with suburb + region as fallback
            fallback = f"{clinic.get('suburb_town', '')}, {clinic.get('region', '')}, New Zealand"
            lat, lng = geocode(fallback)
            if lat is not None:
                supabase_patch(
                    f"/rest/v1/dental_clinics?id=eq.{clinic['id']}",
                    {"lat": lat, "lng": lng},
                )
                print(f"[{i}/{total}] OK* {name} → {lat:.5f}, {lng:.5f}  (fallback)")
                ok += 1
            else:
                print(f"[{i}/{total}] FAIL: {name} | {address}")
                fail += 1

        time.sleep(1)  # Nominatim rate limit: 1 req/sec

    print(f"\nDone. {ok} geocoded, {skip} skipped (no address), {fail} failed.")

if __name__ == "__main__":
    main()
