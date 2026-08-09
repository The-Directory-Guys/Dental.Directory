import os, glob

OLD_JWT = os.environ['SUPABASE_JWT']

for path in glob.glob('*.py'):
    text = open(path, encoding='utf-8').read()
    if OLD_JWT not in text:
        continue
    # Replace the hardcoded string assignment
    new_text = text.replace(f'"{OLD_JWT}"', "os.environ['SUPABASE_JWT']")
    new_text = new_text.replace(f"'{OLD_JWT}'", "os.environ['SUPABASE_JWT']")
    open(path, 'w', encoding='utf-8').write(new_text)
    print(f'Fixed: {path}')

print('Done.')
