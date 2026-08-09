import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

SOURCE = 'https://sparklewhite.co.nz/services'

# 1. Update clinic — category + description
desc = "A cosmetic teeth whitening clinic based in Nelson, run by founder Charmaine McFarlane. Using dental-grade hydrogen peroxide and advanced ultrasonic technology for safe, painless whitening. Treatments range from light to heavy discolouration, with follow-up sessions and home maintenance kits also available. Products are FDA approved and sourced through the NZ Cosmetic Teeth Whitening Association."
print(q(f"""UPDATE dental_clinics
    SET category = 'teeth_whitening',
        description = $${desc}$$
    WHERE id = 2923 RETURNING id, category"""))

# 2. Insert scraped prices
prices = [
    ('Consultation',                    '$60 (15 min)',          'Includes oral cavity inspection and shade matching. If proceeding to treatment on the day, consultation is built into the total price.'),
    ('ULTIMATE Stain Removal',          '$349 (was $799)',       '75 min treatment. Best for heavy discolouration, over-50s, or stubborn staining such as from antibiotics, coffee, or red wine.'),
    ('BOOST Heavy Staining Treatment',  '$299 (was $699)',       '60 min treatment. Activators and desensitising ingredients added. Recommended for medium to heavy staining, ideal for those 30+.'),
    ('WOW Medium Staining Treatment',   '$249 (was $599)',       '60 min treatment. Best for light to medium staining and first-time whitening clients under 30.'),
    ('Follow-up treatment',             '$149 – $199',           '30 min ($149), 45 min ($179), or 60 min ($199). Available to existing clients for deep staining or maintenance every 3–6 months.'),
    ('Home Whitening Kit',              '$149 – $199',           '1 pen + LED light kit ($149) or 2 pens + LED light kit ($199). Dental-grade 6.9% hydrogen peroxide pen. Approx. 20 applications per pen.'),
    ('Gift Voucher',                    'From $50',              'Contact local clinic or purchase online.'),
]
for treatment, price_label, notes in prices:
    res = q(f"""INSERT INTO scraped_prices (clinic_id, treatment, price_label, notes, source_url, source)
        VALUES (2923, $${treatment}$$, $${price_label}$$, $${notes}$$, '{SOURCE}', 'manual:sparklewhite.co.nz')
        ON CONFLICT DO NOTHING RETURNING id""")
    print(f'  {treatment}: {res}')

# 3. Add Charmaine McFarlane as practitioner (owner/founder)
bio = "Founder and owner of Sparklewhite Teeth NZ. A member of the NZ Cosmetic Teeth Whitening Association (NZCTWA) and an experienced cosmetic teeth whitening specialist. Known for her friendly and professional approach, and for guiding clients through the full whitening process with clear explanation and care."
res = q(f"""INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, bio, source_url)
    VALUES (2923, $$Charmaine McFarlane$$, 'F', $$Cosmetic teeth whitening$$, $${bio}$$, 'https://sparklewhite.co.nz/')
    RETURNING id""")
print(f'\nCharmaine McFarlane inserted: {res}')

print('\nDone.')
