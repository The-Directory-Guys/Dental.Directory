import os, glob
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')

OLD_ANON = os.environ['SUPABASE_ANON_KEY']

for path in glob.glob('*.py'):
    text = open(path, encoding='utf-8').read()
    if OLD_ANON not in text:
        continue
    new_text = text.replace(f'"{OLD_ANON}"', "os.environ['SUPABASE_ANON_KEY']")
    new_text = new_text.replace(f"'{OLD_ANON}'", "os.environ['SUPABASE_ANON_KEY']")
    open(path, 'w', encoding='utf-8').write(new_text)
    print(f'Fixed: {path}')

print('Done.')
