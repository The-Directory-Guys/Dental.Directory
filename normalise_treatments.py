"""
Normalise manual:* scraped_prices treatment names in Supabase.

Runs in preview mode by default — shows what would change without touching the DB.
Pass --apply to write changes.

Treatment names are mapped to a standard taxonomy. The original treatment name
is preserved in the `notes` field so no detail is lost.
"""

import json
import os
import re
import sys
import requests
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

# ---------------------------------------------------------------------------
# Normalisation rules
# Priority order matters — first match wins.
# Each entry: (normalised_name, regex_pattern)
# ---------------------------------------------------------------------------

RULES = [
    # -----------------------------------------------------------------------
    # PAYMENT / FINANCE  (check before clinical so "Orthodontics payment plan" → Payment plan)
    # -----------------------------------------------------------------------
    ("Q Card",          r"\bq.?card\b|\bq.?mastercard\b"),
    ("Afterpay",        r"\bafterpay\b|\bgenoapay\b|\boxipay\b|\bhumm\b"),
    ("Laybuy",          r"\blaybuy\b"),
    ("Zip",             r"\bzip\b(?!\s*code)"),
    ("Gem Visa",        r"\bgem.visa\b|\bgem.finance\b"),
    ("Farmers Card",    r"\bfarmers.?(card|finance)\b"),
    ("Finance Now",     r"\bfinance.now\b"),
    ("Loan Haus",       r"\bloan.haus\b"),
    ("MTF Finance",     r"\bmtf.finance\b"),
    ("Alipay / WeChat", r"\balipay\b|\bwechat\b"),
    ("Payment plan",    r"\bpayment.plans?\b|\bpayment.terms\b|\bpayment.options?\b|\bdirect.debit\b|\bin.?house.finance\b|\binterest.?free.?(finance|payment|monthly)\b|\bmonthly.payment\b|\bbuy.now.pay.later\b|\bdental.financ|\bin.office.dental.plans?\b"),
    ("Credit card",     r"\bcredit.card\b"),

    # -----------------------------------------------------------------------
    # INSURANCE
    # -----------------------------------------------------------------------
    ("Southern Cross",  r"\bsouthern.cross\b"),
    ("NIB",             r"\bnib\b(?!.*(implant|dental\s+implant))"),
    ("HealthNow",       r"\bhealthnow\b"),

    # -----------------------------------------------------------------------
    # GOVERNMENT / CONCESSIONS
    # -----------------------------------------------------------------------
    ("ACC",             r"^acc$|^acc\s|\bacc.dental\b|\bacc.injury\b|\bacc.claims\b|\bacc.&.winz\b"),
    ("ACC shortfall",   r"\bacc.shortfall\b"),
    ("WINZ",            r"\bwinz\b"),
    ("Studylink",       r"\bstudylink\b"),
    ("Community Services Card", r"\bcommunity.services.card\b|\bcsc\b"),
    ("SuperGold Card",  r"\bsupergold\b|\bgold.card.discount\b"),
    ("Grey Power",      r"\bgrey.power\b"),
    ("Student discount", r"\bstudent.discount\b|\bstudent.dental\b|\bstudent.check.?up\b|\bstudent.subsid\b|\bara.student\b|\botago.student\b|\buni(versity)?.+student\b|\bstudent.free\b|\bstudent.dental.treat\b"),
    ("Free teen dental care", r"\bfree.teen|\bfree.adolescent|\bfree.dental.care|\bteen.basic|\bministry.funded|\bunder.18.care|\bunder.18s?\b|\badolescent.care|\badolescent.dental|\bteen.dental|\bfree.dental|\bsecondary.school|\byear.9\b|\bteenagers?\s+1[3-8]\b|\bfree.teenage"),
    ("Cancellation fee", r"\bcancellation\b|\bfail.to.attend\b|\bfta.fee\b"),
    ("After-hours fee", r"\bafter.hours\b"),
    ("Capital & Coast DHB discount", r"\bcapital.+coast\b"),
    ("K'aute Pasifika", r"\bk.?aute.pasifika\b"),
    ("Pregnant woman's scheme", r"\bpregnant.woman\b|\bpregnancy.scheme\b"),
    ("Institute discount", r"\binstitute.of.environ"),

    # -----------------------------------------------------------------------
    # DISCOUNTS / OFFERS
    # -----------------------------------------------------------------------
    ("Family discount",   r"\bfamily.discount\b"),
    ("Refer & Reward",    r"\brefer.+reward\b"),
    ("Gift voucher",      r"\bgift.vouchers?\b"),
    ("Prompt payment discount", r"\bprompt.payment\b|\bpayment.in.full.discount\b"),
    ("Corporate discount", r"\bcorporate.discount\b|\bcorporate.employee\b"),

    # -----------------------------------------------------------------------
    # NEW PATIENT OFFERS / PACKAGES
    # -----------------------------------------------------------------------
    ("New patient offer", r"\bnew.patient\b"),

    # -----------------------------------------------------------------------
    # EXAM / CHECKUP
    # -----------------------------------------------------------------------
    ("Exam / checkup",  r"\b(exam|examination|check.?up|recall|full.mouth.check|full.dental.check|full.oral.health|comprehensive.exam|comprehensive.examination|basic.examination|existing.patient.exam|first.consultation|full.mouth.exam|routine.exam|dental.check)\b"),
    ("Consultation",    r"\bconsultation\b|\bgum.health.eval|\bsurgical.assessment\b"),

    # -----------------------------------------------------------------------
    # IMPLANTS  (before Crown so "implant + crown" → Implant)
    # -----------------------------------------------------------------------
    ("Implant – All-on-4", r"\ball.on.four\b|\ball.on.4\b|\bfull.arch\b|\ball.teeth.on.4"),
    ("Implant",            r"\bimplants?\b(?!.*(crown.length))"),

    # -----------------------------------------------------------------------
    # SCALE AND POLISH / HYGIENE
    # -----------------------------------------------------------------------
    ("Periodontal treatment", r"\bperiodontal\b|\broot.plan|\bcause.related.therapy\b|\bdeep.perio\b|\bgum.treatment\b|\bgum.disease\b|\bendoscopic\b|\bperio.scal\b"),
    ("Scale and polish", r"\bscale.and.polish|\bscale.&.polish|\bscale.and.clean|\bclean.and.polish|\bhygien|\bdental.clean|\bteeth.clean|\broutine.clean|\bbasic.scale|\bscale.&.clean|\bregular.maintenance|\bregular.clean|\bclean(?! kit|\s*cut|\s*up)\b|\bdenture.clean"),

    # -----------------------------------------------------------------------
    # FILLINGS
    # -----------------------------------------------------------------------
    ("Filling – composite", r"\bcomposite.fill|\bwhite.fill|\bcomposite.resin.fill|\btooth.coloured.fill|\btooth.color(ed)?.fill|\bcomposite\/white\b|\btooth.colou?red\b"),
    ("Filling – amalgam",   r"\bamalgam\b"),
    ("Filling – glass ionomer", r"\bglass.ionomer\b"),
    ("Filling",             r"\bfillings?\b(?!.*(under|private))|\brestor(ations?|ative)\b(?!.*(implant|crown|veneer))|\bpermanent.dental.fill|\bcomposite\s*\/?\s*amalgam\b"),

    # -----------------------------------------------------------------------
    # EXTRACTIONS
    # -----------------------------------------------------------------------
    ("Extraction – surgical", r"\bsurgical.extract|\bsurgical.wisdom|\bimpacted.wisdom|\bimpacted.tooth|\bsurgical.tooth.extract|\bextract.+surgical\b|\bextract.*–.*surgical\b"),
    ("Extraction – wisdom tooth", r"\bwisdom.tooth.extract|\bwisdom.teeth.remov|\bwisdom.teeth.extract|\bwisdom.teeth.surgic"),
    ("Extraction – simple",  r"\b(simple|basic|conventional|standard|regular|single).extract|\btooth.remov|\bsingle.tooth.extract"),
    ("Extraction",           r"\bextract(ion)?s?\b|\btooth.remov\b"),

    # -----------------------------------------------------------------------
    # ROOT CANALS
    # -----------------------------------------------------------------------
    ("Root canal – front tooth", r"\broot.canal.[-–]?.*(front|anterior|incisor|canine)|\b(anterior|front|incisor|canine).root.canal|\broot.treat.+one.root|\bone.root\b"),
    ("Root canal – premolar",    r"\broot.canal.[-–]?.*(pre.?molar|middle)|\bpre.?molar.root.canal|\broot.treat.+two.root|\btwo.root\b"),
    ("Root canal – molar",       r"\broot.canal.[-–]?.molar|\bmolar.root.canal|\broot.treat.+three.root|\bthree.root\b|\badvanced.level.root.canal|\bcomplex.root.canal"),
    ("Root canal",               r"\broot.canals?\b|\broot.treat(ment)?\b|\brendodontic\b"),

    # -----------------------------------------------------------------------
    # CROWNS
    # -----------------------------------------------------------------------
    ("Crown – ceramic",  r"\b(ceramic|porcelain|zirconia|emax|all.ceramic|full.porcelain).crown|\bcrown.–.all.ceramic|\bcrown.–.porcelain|\bporcelain.fused|\bceramic.restor"),
    ("Crown – gold",     r"\bgold.crown\b|\bgold.metal.crown\b|\bcrown.–.gold\b"),
    ("Crown",            r"\bcrowns?\b(?!.*(length))|\bbridges?\b|\binlay\b|\bonlay\b|\boverlay\b|\brecement\b"),

    # -----------------------------------------------------------------------
    # VENEERS
    # -----------------------------------------------------------------------
    ("Veneer – composite", r"\bcomposite.veneer\b"),
    ("Veneer – porcelain", r"\b(porcelain|ceramic).veneer\b|\bsingle.tooth.porcelain.veneer\b"),
    ("Veneer",             r"\bveneer\b"),

    # -----------------------------------------------------------------------
    # WHITENING
    # -----------------------------------------------------------------------
    ("Whitening – in-chair", r"\b(in.chair|in.clinic|in.office|in.surgery|chairside|zoom).whiten|\bwhiten.+\(approx|\bbleach.+upper.and.lower\b|\btooth.whiten(ing)?\b(?!.*(kit|tray|take.home))|^whitening$|\bwhitening\s*\(chairside\)|\bin.session.whiten|\bin.studio.whiten|\bin.mouth.whiten|\bwhitening\s*-\s*in.house\b"),
    ("Whitening – take-home", r"\btake.?home.whiten|\bat.?home.whiten|\bcustom.whiten.tray|\bcustom.bleach|\bwhitening.kit|\bwhitening.tray|\bwhitening\s*\(take.home|\bwhitening\s*-\s*take.home"),
    ("Whitening",          r"\bwhiten|\bbleach\b|\bconfidence.package\b|\btouch.up.package\b|\bdouble.deal\b"),

    # -----------------------------------------------------------------------
    # DENTURES
    # -----------------------------------------------------------------------
    ("Denture – full",    r"\b(complete|full).dentures?\b|\bupper.and.lower.denture\b|\bfull.dentures?\b|\bcomplete.set.denture\b"),
    ("Denture – partial", r"\b(partial|chrome|metal.partial|plastic.partial|nylon.partial|valplast|acrylic.partial|frame.partial).dentures?\b|\bdenture[s]?.–.(metal|plastic|nylon)\b"),
    ("Denture repair",    r"\bdenture.repair\b|\bdenture.reline\b|\breline\b|\binsurance.claims.+denture\b"),
    ("Denture",           r"\bdentures?\b"),

    # -----------------------------------------------------------------------
    # X-RAYS
    # -----------------------------------------------------------------------
    ("X-ray – OPG",      r"\bopg\b|\bpanoramic.x.?ray\b|\bpanoramic.jaw.scan\b|\borthopantomogram\b|\bcbct\b|\bcone.beam\b|\b3d.?scan\b|\b3d.?x.?ray\b|\bfull.mouth.periapical\b"),
    ("X-ray – intraoral", r"\bintraoral.x.?ray\b|\bbitewing\b|\bperiapical\b|\bpa.x.?ray\b|\bpbw\b|\bin.mouth.x.?ray\b|\bx.?ray.each\b|\bx.?rays.of.back"),
    ("X-ray",            r"\bx.?rays?\b|\bradiographs?\b"),

    # -----------------------------------------------------------------------
    # ORTHODONTICS
    # -----------------------------------------------------------------------
    ("Orthodontics – aligners", r"\binvisalign\b|\bclear.aligner\b|\baligner\b|\btracks\b"),
    ("Orthodontics – braces",   r"\bbraces\b|\bfixed.orthodontic\b|\bfastbraces\b"),
    ("Orthodontics",            r"\bordhodontics?\b|\borthodontics?\b|\bfunctional.orthod|\bretainer\b"),

    # -----------------------------------------------------------------------
    # MOUTHGUARDS / NIGHTGUARDS
    # -----------------------------------------------------------------------
    ("Night guard",    r"\bnight.guard\b|\bocclusal.splint\b|\bsplint\b|\bsnoring.appliance\b|\btap.appliance\b|\bthornton\b"),
    ("Mouthguard",     r"\bmouthguard\b|\bsports.guard\b|\bsports.mouthguard\b"),

    # -----------------------------------------------------------------------
    # PERIODONTAL SURGERY
    # -----------------------------------------------------------------------
    ("Bone graft",     r"\bbone.graft\b|\bsinus.lift\b|\bgbr\b"),
    ("Gum graft",      r"\bgum.graft\b|\bconnective.tissue.graft\b|\bfgg\b|\bfree.gingival\b"),
    ("Crown lengthening", r"\bcrown.lengthen|\bgum.lift|\baesthetic.crown|\brecession|\bcosmetic.gum.surg"),
    ("Flap surgery",   r"\bflap.surgery\b|\bpericision\b"),

    # -----------------------------------------------------------------------
    # SEDATION / ANAESTHESIA
    # -----------------------------------------------------------------------
    ("IV sedation",    r"\biv.sedation\b|\bintravenous.sedation\b|\bgeneral.anaesthesia\b"),

    # -----------------------------------------------------------------------
    # FISSURE SEALANTS / FLUORIDE
    # -----------------------------------------------------------------------
    ("Fissure sealant", r"\bfissure.sealant\b"),
    ("Fluoride",        r"\bfluoride\b"),

    # -----------------------------------------------------------------------
    # TOOTH GEMS
    # -----------------------------------------------------------------------
    ("Tooth gem",       r"\btooth.gem\b|\bswarovski\b|\bgem.+appointment\b"),

    # -----------------------------------------------------------------------
    # CHILDREN'S DENTISTRY
    # -----------------------------------------------------------------------
    ("Children's dentistry", r"\bchild(ren)?'?s?\s*(dent|fill|extract|check)|\bpaediatric.dent|\bkids.dent|\bchildren.under.13|\bfillings?\s*\(under"),

    # -----------------------------------------------------------------------
    # MISC CLINICAL
    # -----------------------------------------------------------------------
    ("Dental plan / membership", r"\bdental.plan\b|\bdental.wellness\b|\bmembership\b"),
    ("Botox / aesthetics", r"\bbotox\b|\bdysport\b|\bdermal\b|\baesthetic.inject\b"),
    ("Laser treatment", r"\bdiode.laser\b|\blaser.treat\b|\bfrenectomy\b"),
    ("Space maintainer", r"\bspace.maintainer\b"),
    ("Diagnostic wax-up", r"\bwax.up\b|\bstudy.model\b|\bsmile.test.drive\b"),
    ("Mobile service",  r"\bmobile.service\b"),
    ("Custom design",   r"\bcustom.design\b"),
]


def normalise(treatment: str) -> str | None:
    """Return the normalised treatment name, or None if no rule matches."""
    t = treatment.strip()
    for name, pattern in RULES:
        if re.search(pattern, t, re.IGNORECASE):
            return name
    return None


# ---------------------------------------------------------------------------
# Fetch / update
# ---------------------------------------------------------------------------

def fetch_manual_rows() -> list[dict]:
    rows = []
    page_size = 1000
    offset = 0
    while True:
        url = (
            f"{SUPABASE_URL}/rest/v1/scraped_prices"
            f"?select=id,treatment,price_label,price_nzd,notes,source"
            f"&source=like.manual:*"
            f"&order=id.asc"
            f"&limit={page_size}&offset={offset}"
        )
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        batch = resp.json()
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def update_row(row_id: int, new_treatment: str, new_notes: str | None):
    payload = {"treatment": new_treatment}
    if new_notes is not None:
        payload["notes"] = new_notes
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/scraped_prices?id=eq.{row_id}",
        headers=HEADERS, json=payload, timeout=15,
    )
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    apply = "--apply" in sys.argv

    print("Fetching manual rows...")
    rows = fetch_manual_rows()
    print(f"  {len(rows)} rows fetched")

    changes = []
    unmapped = defaultdict(int)

    for row in rows:
        original = row["treatment"]
        normalised = normalise(original)

        if normalised is None:
            unmapped[original] += 1
            continue

        if normalised == original:
            continue  # already correct

        # Build notes: preserve original treatment name if notes is empty
        existing_notes = (row.get("notes") or "").strip()
        if existing_notes:
            new_notes = existing_notes  # don't overwrite existing notes
        else:
            new_notes = original  # save original as notes

        changes.append({
            "id":          row["id"],
            "original":    original,
            "normalised":  normalised,
            "new_notes":   new_notes,
        })

    print(f"\n{'APPLYING' if apply else 'PREVIEW'}: {len(changes)} rows would change")

    # Group by original → normalised for readability
    by_change = defaultdict(list)
    for c in changes:
        by_change[(c["original"], c["normalised"])].append(c["id"])

    def safe(s):
        return s.encode("ascii", "replace").decode()

    print("\n--- Changes ---")
    for (orig, norm), ids in sorted(by_change.items(), key=lambda x: x[0][1]):
        print(f"  {safe(orig)!r:55s} -> {safe(norm)!r}  ({len(ids)} rows)")

    if unmapped:
        print(f"\n--- Unmapped ({len(unmapped)} distinct, {sum(unmapped.values())} rows) ---")
        for t, count in sorted(unmapped.items(), key=lambda x: -x[1]):
            print(f"  {count:3d}x  {safe(t)}")

    if apply:
        print(f"\nApplying {len(changes)} updates...")
        for i, c in enumerate(changes):
            update_row(c["id"], c["normalised"], c["new_notes"])
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{len(changes)}")
        print("Done.")
    else:
        print(f"\nRun with --apply to write changes to Supabase.")


if __name__ == "__main__":
    main()
