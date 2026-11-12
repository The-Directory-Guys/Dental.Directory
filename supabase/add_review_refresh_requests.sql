-- Lets a signed-in clinic owner request a Google reviews refresh from manage.html,
-- without ever calling SerpAPI directly from the browser (that key must stay
-- server-side, and matching still needs a human check - see chat for why).
-- Emails dentalcomparenz@gmail.com via the same Resend-via-pg_net mechanism as
-- add_claim_notification.sql, reusing the same 'resend_api_key' Vault secret
-- (already configured if claim notifications are working).
-- Run once in the Supabase SQL Editor.

CREATE TABLE IF NOT EXISTS review_refresh_requests (
  id bigserial primary key,
  clinic_id bigint not null references dental_clinics(id) on delete cascade,
  requested_by uuid references auth.users(id) on delete set null,
  status text not null default 'pending',
  requested_at timestamptz default now()
);

-- Only one outstanding request per clinic at a time - a second click (or a
-- second tab) just hits this instead of queuing a duplicate notification.
CREATE UNIQUE INDEX IF NOT EXISTS review_refresh_requests_one_pending_per_clinic
  ON review_refresh_requests (clinic_id) WHERE (status = 'pending');

ALTER TABLE review_refresh_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Owners request refresh for their own clinic" ON review_refresh_requests
  FOR INSERT
  WITH CHECK (clinic_id IN (SELECT clinic_id FROM clinic_owners WHERE user_id = auth.uid()));
CREATE POLICY "Owners view their own clinic's requests" ON review_refresh_requests
  FOR SELECT
  USING (clinic_id IN (SELECT clinic_id FROM clinic_owners WHERE user_id = auth.uid()));
CREATE POLICY "admin_manage_review_requests" ON review_refresh_requests
  FOR ALL USING (auth.role() = 'service_role');

CREATE OR REPLACE FUNCTION public.notify_review_refresh_request()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  api_key text;
  clinic_name text;
  email_html text;
BEGIN
  SELECT decrypted_secret INTO api_key
  FROM vault.decrypted_secrets
  WHERE name = 'resend_api_key'
  LIMIT 1;

  IF api_key IS NULL THEN
    RETURN new; -- secret not configured yet - skip silently, same as add_claim_notification.sql
  END IF;

  SELECT name INTO clinic_name FROM dental_clinics WHERE id = new.clinic_id;

  email_html := format(
    '<p>A clinic owner requested a Google reviews refresh.</p>' ||
    '<p><strong>Clinic:</strong> %s (id %s)</p>',
    coalesce(clinic_name, 'Unknown'), new.clinic_id
  );

  PERFORM net.http_post(
    url := 'https://api.resend.com/emails',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || api_key
    ),
    body := jsonb_build_object(
      'from', 'Dental Compare <no-reply@dentalcompare.co.nz>',
      'to', array['dentalcomparenz@gmail.com'],
      'subject', 'Review refresh requested: ' || coalesce(clinic_name, 'Unknown clinic'),
      'html', email_html
    )
  );

  RETURN new;
END;
$$;

DROP TRIGGER IF EXISTS on_review_refresh_requested ON review_refresh_requests;

CREATE TRIGGER on_review_refresh_requested
  AFTER INSERT ON review_refresh_requests
  FOR EACH ROW
  EXECUTE FUNCTION public.notify_review_refresh_request();
