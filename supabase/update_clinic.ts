import { createClient } from '@supabase/supabase-js';
import * as fs from 'fs';
import * as path from 'path';

function loadEnv() {
  const envPath = path.join(process.cwd(), '.env');
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, 'utf-8').split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith('#')) continue;
    const eq = t.indexOf('=');
    if (eq === -1) continue;
    const key = t.slice(0, eq).trim();
    let val = t.slice(eq + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) val = val.slice(1, -1);
    if (!process.env[key]) process.env[key] = val;
  }
}
loadEnv();

const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_KEY!);

async function run() {
  const { error } = await supabase
    .from('dental_clinics')
    .update({ services: 'General Dentistry,Cosmetic,Teeth Whitening,Dental Implants,Emergency,Orthodontics' })
    .eq('id', 1261);

  if (error) console.error('Error:', error);
  else console.log('Updated Bradley Wood Dentists (id 1261) → General Dentistry,Cosmetic,Teeth Whitening,Dental Implants,Emergency,Orthodontics');
}
run();
