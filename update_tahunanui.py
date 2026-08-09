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

print('Current description:')
print(q("SELECT description FROM dental_clinics WHERE id = 1681"))

# 1. Clear membership_plans — already captured in SuperGold Card scraped_price entry
print(q("UPDATE clinic_amenities SET membership_plans = NULL WHERE clinic_id = 1681"))
print('  membership_plans cleared')

# 2. Update SuperGold Card price_label to make it self-contained
print(q("""UPDATE scraped_prices
    SET price_label = 'SuperGold Card and Grey Power New Zealand member discounts available'
    WHERE clinic_id = 1681 AND treatment = 'SuperGold Card'"""))
print('  SuperGold Card label updated')

# 3. Update description from website
desc = "Serving the Nelson and Tasman communities since 1986, offering a full range of professional dental services in a modern and welcoming clinic. As a family-orientated practice, the approach has always been excellent dentistry at affordable prices. Special emphasis is placed on caring for nervous and anxious patients."
print(q(f"UPDATE dental_clinics SET description = $${desc}$$ WHERE id = 1681"))
print('  Description updated')

# Verify
print()
print(q("SELECT description FROM dental_clinics WHERE id = 1681"))
print(q("SELECT treatment, price_label FROM scraped_prices WHERE clinic_id = 1681"))
print(q("SELECT payment_partners, membership_plans FROM clinic_amenities WHERE clinic_id = 1681"))
