


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE SCHEMA IF NOT EXISTS "public";


ALTER SCHEMA "public" OWNER TO "pg_database_owner";


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE OR REPLACE FUNCTION "public"."auto_link_clinic_owner"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
declare
  matched_clinic_id bigint;
begin
  select id into matched_clinic_id
  from dental_clinics
  where lower(email) = lower(new.email)
  limit 1;

  if matched_clinic_id is not null then
    insert into clinic_owners (user_id, clinic_id)
    values (new.id, matched_clinic_id)
    on conflict do nothing;
  end if;

  return new;
end;
$$;


ALTER FUNCTION "public"."auto_link_clinic_owner"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."notify_new_claim"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
declare
  api_key text;
  clinic_name text;
  email_html text;
begin
  select decrypted_secret into api_key
  from vault.decrypted_secrets
  where name = 'resend_api_key'
  limit 1;

  if api_key is null then
    -- Secret not configured yet - skip silently rather than failing the claim insert.
    return new;
  end if;

  select name into clinic_name from dental_clinics where id = new.clinic_id;

  email_html := format(
    '<p>New clinic claim submitted.</p>' ||
    '<p><strong>Clinic:</strong> %s (id %s)</p>' ||
    '<p><strong>Name:</strong> %s<br>' ||
    '<strong>Role:</strong> %s<br>' ||
    '<strong>Email:</strong> %s<br>' ||
    '<strong>Phone:</strong> %s</p>' ||
    '<p><strong>Message:</strong> %s</p>',
    coalesce(clinic_name, 'Unknown'), new.clinic_id,
    coalesce(new.name, ''), coalesce(new.role, ''),
    coalesce(new.email, ''), coalesce(new.phone, ''),
    coalesce(new.message, '(none)')
  );

  perform net.http_post(
    url := 'https://api.resend.com/emails',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || api_key
    ),
    body := jsonb_build_object(
      'from', 'Dental Compare <no-reply@dentalcompare.co.nz>',
      'to', array['dentalcomparenz@gmail.com'],
      'subject', 'New clinic claim: ' || coalesce(clinic_name, 'Unknown clinic'),
      'html', email_html
    )
  );

  return new;
end;
$$;


ALTER FUNCTION "public"."notify_new_claim"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."clinic_amenities" (
    "clinic_id" bigint NOT NULL,
    "parking_access" "text",
    "wheelchair_accessible" boolean,
    "same_day_emergency" boolean,
    "saturday_evening_hours" boolean,
    "in_house_specialists" "text",
    "practice_size" "text",
    "sedation_options" "text",
    "calming_amenities" "text",
    "dental_anxiety_friendly" boolean,
    "years_open" "text",
    "awards" "text"[],
    "professional_memberships" "text"[],
    "before_after_gallery" boolean,
    "online_booking" boolean,
    "new_patient_forms_online" boolean,
    "payment_partners" "text",
    "membership_plans" "text",
    "kids_family_friendly" "text",
    "source" "text",
    "source_url" "text",
    "scraped_at" "date" DEFAULT CURRENT_DATE,
    "special_offers" "text",
    "online_booking_note" "text",
    "wheelchair_accessible_note" "text",
    "dental_anxiety_friendly_note" "text",
    "kids_family_friendly_note" "text",
    "same_day_emergency_note" "text",
    "online_booking_link" "text"
);


ALTER TABLE "public"."clinic_amenities" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."clinic_claims" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "clinic_id" integer,
    "name" "text" NOT NULL,
    "email" "text" NOT NULL,
    "phone" "text",
    "role" "text",
    "message" "text",
    "status" "text" DEFAULT 'pending'::"text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."clinic_claims" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."clinic_owners" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "clinic_id" integer NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."clinic_owners" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."clinic_photos" (
    "id" bigint NOT NULL,
    "clinic_id" bigint NOT NULL,
    "url" "text" NOT NULL,
    "sort_order" integer DEFAULT 0 NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."clinic_photos" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."clinic_photos_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."clinic_photos_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."clinic_photos_id_seq" OWNED BY "public"."clinic_photos"."id";



CREATE TABLE IF NOT EXISTS "public"."clinic_practitioners" (
    "id" bigint NOT NULL,
    "clinic_id" bigint NOT NULL,
    "name" "text" NOT NULL,
    "photo_url" "text",
    "experience" "text",
    "specialties" "text",
    "bio" "text",
    "languages" "text",
    "source_url" "text",
    "scraped_at" "date" DEFAULT CURRENT_DATE,
    "gender" "text",
    "photo_checked" boolean,
    "qualifications" "text",
    CONSTRAINT "clinic_practitioners_gender_check" CHECK (("gender" = ANY (ARRAY['M'::"text", 'F'::"text"])))
);


ALTER TABLE "public"."clinic_practitioners" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."clinic_practitioners_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."clinic_practitioners_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."clinic_practitioners_id_seq" OWNED BY "public"."clinic_practitioners"."id";



CREATE TABLE IF NOT EXISTS "public"."dental_clinics" (
    "name" "text" NOT NULL,
    "address" "text",
    "phone_national" "text",
    "phone_international" "text",
    "website" "text",
    "rating" double precision,
    "total_ratings" bigint,
    "business_status" "text",
    "google_maps_url" "text",
    "opening_hours" "text",
    "category" "text",
    "region" "text",
    "suburb_town" "text",
    "price" "text",
    "date_scraped" "text",
    "id" bigint NOT NULL,
    "city" "text",
    "prices_last_updated" "date",
    "open_to_new_patients" boolean,
    "legal_business_name" "text",
    "description" "text",
    "services" "text",
    "lat" double precision,
    "lng" double precision,
    "photo_url" "text",
    "founded_year" integer,
    "facebook_url" "text",
    "clinic_photo_url" "text",
    "email" "text",
    "booking_url" "text"
);


ALTER TABLE "public"."dental_clinics" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."dental_clinics_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."dental_clinics_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."dental_clinics_id_seq" OWNED BY "public"."dental_clinics"."id";



CREATE TABLE IF NOT EXISTS "public"."feedback" (
    "id" bigint NOT NULL,
    "page_url" "text",
    "found_it" boolean,
    "comment" "text",
    "overall_rating" smallint,
    "aspect_ratings" "jsonb",
    "submitted_at" timestamp with time zone DEFAULT "now"(),
    "user_agent" "text"
);


ALTER TABLE "public"."feedback" OWNER TO "postgres";


ALTER TABLE "public"."feedback" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "public"."feedback_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);



CREATE TABLE IF NOT EXISTS "public"."google_reviews" (
    "id" bigint NOT NULL,
    "clinic_id" bigint NOT NULL,
    "author" "text",
    "rating" integer,
    "date_text" "text",
    "snippet" "text",
    "fetched_at" timestamp with time zone DEFAULT "now"(),
    "is_curated" boolean DEFAULT false,
    "is_curated_rating" boolean DEFAULT false,
    "owner_reply" "text",
    "owner_reply_at" timestamp with time zone,
    CONSTRAINT "google_reviews_rating_check" CHECK ((("rating" >= 1) AND ("rating" <= 5)))
);


ALTER TABLE "public"."google_reviews" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."google_reviews_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."google_reviews_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."google_reviews_id_seq" OWNED BY "public"."google_reviews"."id";



CREATE TABLE IF NOT EXISTS "public"."price_reports" (
    "id" bigint NOT NULL,
    "clinic_id" bigint,
    "user_id" "uuid",
    "treatment" "text" NOT NULL,
    "price_nzd" integer NOT NULL,
    "notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."price_reports" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."price_reports_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."price_reports_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."price_reports_id_seq" OWNED BY "public"."price_reports"."id";



CREATE TABLE IF NOT EXISTS "public"."price_submissions" (
    "id" bigint NOT NULL,
    "clinic_id" integer,
    "clinic_name" "text",
    "user_handle" "text" NOT NULL,
    "submission_type" "text" NOT NULL,
    "price" integer,
    "value_text" "text",
    "notes" "text",
    "status" "text" DEFAULT 'pending'::"text" NOT NULL,
    "submitted_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "user_agent" "text",
    "user_id" "uuid"
);


ALTER TABLE "public"."price_submissions" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."price_submissions_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."price_submissions_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."price_submissions_id_seq" OWNED BY "public"."price_submissions"."id";



CREATE TABLE IF NOT EXISTS "public"."reviews" (
    "id" bigint NOT NULL,
    "clinic_id" bigint,
    "user_id" "uuid",
    "rating" integer,
    "body" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "reviews_rating_check" CHECK ((("rating" >= 1) AND ("rating" <= 5)))
);


ALTER TABLE "public"."reviews" OWNER TO "postgres";


CREATE SEQUENCE IF NOT EXISTS "public"."reviews_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."reviews_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."reviews_id_seq" OWNED BY "public"."reviews"."id";



CREATE TABLE IF NOT EXISTS "public"."scraped_prices" (
    "id" bigint NOT NULL,
    "clinic_id" bigint,
    "source" "text" NOT NULL,
    "treatment" "text" NOT NULL,
    "price_nzd" integer,
    "price_label" "text" NOT NULL,
    "source_url" "text" NOT NULL,
    "scraped_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "notes" "text"
);


ALTER TABLE "public"."scraped_prices" OWNER TO "postgres";


COMMENT ON TABLE "public"."scraped_prices" IS 'Website-scraped offers/fees; clinic_id null = chain-wide / not tied to one practice row';



COMMENT ON COLUMN "public"."scraped_prices"."source" IS 'e.g. lumino_pricing_pages';



COMMENT ON COLUMN "public"."scraped_prices"."price_nzd" IS 'Whole NZ dollars when known; null for percentage-only or descriptive offers';



CREATE SEQUENCE IF NOT EXISTS "public"."scraped_prices_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE "public"."scraped_prices_id_seq" OWNER TO "postgres";


ALTER SEQUENCE "public"."scraped_prices_id_seq" OWNED BY "public"."scraped_prices"."id";



ALTER TABLE ONLY "public"."clinic_photos" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."clinic_photos_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."clinic_practitioners" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."clinic_practitioners_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."dental_clinics" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."dental_clinics_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."google_reviews" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."google_reviews_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."price_reports" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."price_reports_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."price_submissions" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."price_submissions_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."reviews" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."reviews_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."scraped_prices" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."scraped_prices_id_seq"'::"regclass");



ALTER TABLE ONLY "public"."clinic_amenities"
    ADD CONSTRAINT "clinic_amenities_pkey" PRIMARY KEY ("clinic_id");



ALTER TABLE ONLY "public"."clinic_claims"
    ADD CONSTRAINT "clinic_claims_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."clinic_owners"
    ADD CONSTRAINT "clinic_owners_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."clinic_owners"
    ADD CONSTRAINT "clinic_owners_user_id_key" UNIQUE ("user_id");



ALTER TABLE ONLY "public"."clinic_photos"
    ADD CONSTRAINT "clinic_photos_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."clinic_practitioners"
    ADD CONSTRAINT "clinic_practitioners_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."dental_clinics"
    ADD CONSTRAINT "dental_clinics_id_key" UNIQUE ("id");



ALTER TABLE ONLY "public"."dental_clinics"
    ADD CONSTRAINT "dental_clinics_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."feedback"
    ADD CONSTRAINT "feedback_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."google_reviews"
    ADD CONSTRAINT "google_reviews_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."google_reviews"
    ADD CONSTRAINT "google_reviews_unique_review" UNIQUE NULLS NOT DISTINCT ("clinic_id", "author", "date_text");



ALTER TABLE ONLY "public"."price_reports"
    ADD CONSTRAINT "price_reports_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."price_submissions"
    ADD CONSTRAINT "price_submissions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."reviews"
    ADD CONSTRAINT "reviews_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."scraped_prices"
    ADD CONSTRAINT "scraped_prices_pkey" PRIMARY KEY ("id");



CREATE UNIQUE INDEX "dental_clinics_google_maps_url_uidx" ON "public"."dental_clinics" USING "btree" ("google_maps_url") WHERE (("google_maps_url" IS NOT NULL) AND ("btrim"("google_maps_url") <> ''::"text"));



CREATE INDEX "google_reviews_clinic_id_idx" ON "public"."google_reviews" USING "btree" ("clinic_id");



CREATE INDEX "google_reviews_rating_idx" ON "public"."google_reviews" USING "btree" ("rating" DESC);



CREATE INDEX "idx_clinic_practitioners_clinic_id" ON "public"."clinic_practitioners" USING "btree" ("clinic_id");



CREATE INDEX "price_reports_clinic_id_idx" ON "public"."price_reports" USING "btree" ("clinic_id");



CREATE INDEX "reviews_clinic_id_idx" ON "public"."reviews" USING "btree" ("clinic_id");



CREATE INDEX "scraped_prices_clinic_id_idx" ON "public"."scraped_prices" USING "btree" ("clinic_id");



CREATE INDEX "scraped_prices_source_idx" ON "public"."scraped_prices" USING "btree" ("source");



CREATE OR REPLACE TRIGGER "on_clinic_claim_created" AFTER INSERT ON "public"."clinic_claims" FOR EACH ROW EXECUTE FUNCTION "public"."notify_new_claim"();



ALTER TABLE ONLY "public"."clinic_amenities"
    ADD CONSTRAINT "clinic_amenities_clinic_id_fkey" FOREIGN KEY ("clinic_id") REFERENCES "public"."dental_clinics"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."clinic_claims"
    ADD CONSTRAINT "clinic_claims_clinic_id_fkey" FOREIGN KEY ("clinic_id") REFERENCES "public"."dental_clinics"("id");



ALTER TABLE ONLY "public"."clinic_owners"
    ADD CONSTRAINT "clinic_owners_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."clinic_photos"
    ADD CONSTRAINT "clinic_photos_clinic_id_fkey" FOREIGN KEY ("clinic_id") REFERENCES "public"."dental_clinics"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."clinic_practitioners"
    ADD CONSTRAINT "clinic_practitioners_clinic_id_fkey" FOREIGN KEY ("clinic_id") REFERENCES "public"."dental_clinics"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."google_reviews"
    ADD CONSTRAINT "google_reviews_clinic_id_fkey" FOREIGN KEY ("clinic_id") REFERENCES "public"."dental_clinics"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."price_reports"
    ADD CONSTRAINT "price_reports_clinic_id_fkey" FOREIGN KEY ("clinic_id") REFERENCES "public"."dental_clinics"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."price_reports"
    ADD CONSTRAINT "price_reports_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."price_submissions"
    ADD CONSTRAINT "price_submissions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."reviews"
    ADD CONSTRAINT "reviews_clinic_id_fkey" FOREIGN KEY ("clinic_id") REFERENCES "public"."dental_clinics"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."reviews"
    ADD CONSTRAINT "reviews_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."scraped_prices"
    ADD CONSTRAINT "scraped_prices_clinic_id_fkey" FOREIGN KEY ("clinic_id") REFERENCES "public"."dental_clinics"("id") ON DELETE CASCADE;



CREATE POLICY "Anyone can view" ON "public"."price_submissions" FOR SELECT USING (true);



CREATE POLICY "Authenticated users can also view practitioners" ON "public"."clinic_practitioners" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "Authenticated users can also view reviews" ON "public"."google_reviews" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "Authenticated users can submit" ON "public"."price_submissions" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Clinic owners can manage their own amenities" ON "public"."clinic_amenities" TO "authenticated" USING (("clinic_id" IN ( SELECT "clinic_owners"."clinic_id"
   FROM "public"."clinic_owners"
  WHERE ("clinic_owners"."user_id" = "auth"."uid"())))) WITH CHECK (("clinic_id" IN ( SELECT "clinic_owners"."clinic_id"
   FROM "public"."clinic_owners"
  WHERE ("clinic_owners"."user_id" = "auth"."uid"()))));



CREATE POLICY "Clinic owners can reply to their own reviews" ON "public"."google_reviews" FOR UPDATE USING (("clinic_id" IN ( SELECT "clinic_owners"."clinic_id"
   FROM "public"."clinic_owners"
  WHERE ("clinic_owners"."user_id" = "auth"."uid"())))) WITH CHECK (("clinic_id" IN ( SELECT "clinic_owners"."clinic_id"
   FROM "public"."clinic_owners"
  WHERE ("clinic_owners"."user_id" = "auth"."uid"()))));



CREATE POLICY "Clinic owners can update their own practitioners" ON "public"."clinic_practitioners" FOR UPDATE USING (("clinic_id" IN ( SELECT "clinic_owners"."clinic_id"
   FROM "public"."clinic_owners"
  WHERE ("clinic_owners"."user_id" = "auth"."uid"())))) WITH CHECK (("clinic_id" IN ( SELECT "clinic_owners"."clinic_id"
   FROM "public"."clinic_owners"
  WHERE ("clinic_owners"."user_id" = "auth"."uid"()))));



CREATE POLICY "Clinic owners manage their own photos" ON "public"."clinic_photos" USING (("clinic_id" IN ( SELECT "clinic_owners"."clinic_id"
   FROM "public"."clinic_owners"
  WHERE ("clinic_owners"."user_id" = "auth"."uid"())))) WITH CHECK (("clinic_id" IN ( SELECT "clinic_owners"."clinic_id"
   FROM "public"."clinic_owners"
  WHERE ("clinic_owners"."user_id" = "auth"."uid"()))));



CREATE POLICY "Enable read access for all users" ON "public"."dental_clinics" FOR SELECT USING (true);



CREATE POLICY "Google reviews are public" ON "public"."google_reviews" FOR SELECT USING (true);



CREATE POLICY "Prices are public" ON "public"."price_reports" FOR SELECT USING (true);



CREATE POLICY "Public can view clinic photos" ON "public"."clinic_photos" FOR SELECT USING (true);



CREATE POLICY "Public read access" ON "public"."clinic_amenities" FOR SELECT USING (true);



CREATE POLICY "Public read access" ON "public"."clinic_practitioners" FOR SELECT USING (true);



CREATE POLICY "Reviews are public" ON "public"."reviews" FOR SELECT USING (true);



CREATE POLICY "Scraped prices are public" ON "public"."scraped_prices" FOR SELECT USING (true);



CREATE POLICY "Users delete own prices" ON "public"."price_reports" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users delete own reviews" ON "public"."reviews" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users insert own prices" ON "public"."price_reports" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users insert own reviews" ON "public"."reviews" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "admin_manage_owners" ON "public"."clinic_owners" USING (("auth"."role"() = 'service_role'::"text"));



CREATE POLICY "admin_read_claims" ON "public"."clinic_claims" FOR SELECT USING (("auth"."role"() = 'service_role'::"text"));



CREATE POLICY "admin_update_claims" ON "public"."clinic_claims" FOR UPDATE USING (("auth"."role"() = 'service_role'::"text"));



CREATE POLICY "anon_insert_claims" ON "public"."clinic_claims" FOR INSERT TO "anon" WITH CHECK (true);



CREATE POLICY "anon_insert_feedback" ON "public"."feedback" FOR INSERT TO "anon" WITH CHECK (true);



ALTER TABLE "public"."clinic_amenities" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."clinic_claims" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."clinic_owners" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."clinic_photos" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."clinic_practitioners" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."dental_clinics" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."feedback" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."google_reviews" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "owner_read_own" ON "public"."clinic_owners" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "owners manage own pricing" ON "public"."scraped_prices" TO "authenticated" USING (("clinic_id" IN ( SELECT "clinic_owners"."clinic_id"
   FROM "public"."clinic_owners"
  WHERE ("clinic_owners"."user_id" = "auth"."uid"()))));



CREATE POLICY "owners read own" ON "public"."clinic_owners" FOR SELECT TO "authenticated" USING (("auth"."uid"() = "user_id"));



CREATE POLICY "owners update own clinic" ON "public"."dental_clinics" FOR UPDATE TO "authenticated" USING (("id" IN ( SELECT "clinic_owners"."clinic_id"
   FROM "public"."clinic_owners"
  WHERE ("clinic_owners"."user_id" = "auth"."uid"()))));



ALTER TABLE "public"."price_reports" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."price_submissions" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "public read clinics" ON "public"."dental_clinics" FOR SELECT USING (true);



CREATE POLICY "public read prices" ON "public"."scraped_prices" FOR SELECT USING (true);



ALTER TABLE "public"."reviews" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."scraped_prices" ENABLE ROW LEVEL SECURITY;


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";



GRANT ALL ON FUNCTION "public"."auto_link_clinic_owner"() TO "anon";
GRANT ALL ON FUNCTION "public"."auto_link_clinic_owner"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."auto_link_clinic_owner"() TO "service_role";



GRANT ALL ON FUNCTION "public"."notify_new_claim"() TO "anon";
GRANT ALL ON FUNCTION "public"."notify_new_claim"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."notify_new_claim"() TO "service_role";



GRANT ALL ON TABLE "public"."clinic_amenities" TO "anon";
GRANT ALL ON TABLE "public"."clinic_amenities" TO "authenticated";
GRANT ALL ON TABLE "public"."clinic_amenities" TO "service_role";



GRANT ALL ON TABLE "public"."clinic_claims" TO "anon";
GRANT ALL ON TABLE "public"."clinic_claims" TO "authenticated";
GRANT ALL ON TABLE "public"."clinic_claims" TO "service_role";



GRANT ALL ON TABLE "public"."clinic_owners" TO "anon";
GRANT ALL ON TABLE "public"."clinic_owners" TO "authenticated";
GRANT ALL ON TABLE "public"."clinic_owners" TO "service_role";



GRANT ALL ON TABLE "public"."clinic_photos" TO "anon";
GRANT ALL ON TABLE "public"."clinic_photos" TO "authenticated";
GRANT ALL ON TABLE "public"."clinic_photos" TO "service_role";



GRANT ALL ON SEQUENCE "public"."clinic_photos_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."clinic_photos_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."clinic_photos_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."clinic_practitioners" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."clinic_practitioners" TO "authenticated";
GRANT ALL ON TABLE "public"."clinic_practitioners" TO "service_role";



GRANT UPDATE("photo_url") ON TABLE "public"."clinic_practitioners" TO "authenticated";



GRANT UPDATE("experience") ON TABLE "public"."clinic_practitioners" TO "authenticated";



GRANT UPDATE("specialties") ON TABLE "public"."clinic_practitioners" TO "authenticated";



GRANT UPDATE("bio") ON TABLE "public"."clinic_practitioners" TO "authenticated";



GRANT UPDATE("languages") ON TABLE "public"."clinic_practitioners" TO "authenticated";



GRANT UPDATE("gender") ON TABLE "public"."clinic_practitioners" TO "authenticated";



GRANT UPDATE("qualifications") ON TABLE "public"."clinic_practitioners" TO "authenticated";



GRANT ALL ON SEQUENCE "public"."clinic_practitioners_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."clinic_practitioners_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."clinic_practitioners_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."dental_clinics" TO "anon";
GRANT ALL ON TABLE "public"."dental_clinics" TO "authenticated";
GRANT ALL ON TABLE "public"."dental_clinics" TO "service_role";



GRANT ALL ON SEQUENCE "public"."dental_clinics_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."dental_clinics_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."dental_clinics_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."feedback" TO "anon";
GRANT ALL ON TABLE "public"."feedback" TO "authenticated";
GRANT ALL ON TABLE "public"."feedback" TO "service_role";



GRANT ALL ON SEQUENCE "public"."feedback_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."feedback_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."feedback_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."google_reviews" TO "anon";
GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."google_reviews" TO "authenticated";
GRANT ALL ON TABLE "public"."google_reviews" TO "service_role";



GRANT UPDATE("owner_reply") ON TABLE "public"."google_reviews" TO "authenticated";



GRANT UPDATE("owner_reply_at") ON TABLE "public"."google_reviews" TO "authenticated";



GRANT ALL ON SEQUENCE "public"."google_reviews_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."google_reviews_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."google_reviews_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."price_reports" TO "anon";
GRANT ALL ON TABLE "public"."price_reports" TO "authenticated";
GRANT ALL ON TABLE "public"."price_reports" TO "service_role";



GRANT ALL ON SEQUENCE "public"."price_reports_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."price_reports_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."price_reports_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."price_submissions" TO "anon";
GRANT ALL ON TABLE "public"."price_submissions" TO "authenticated";
GRANT ALL ON TABLE "public"."price_submissions" TO "service_role";



GRANT ALL ON SEQUENCE "public"."price_submissions_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."price_submissions_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."price_submissions_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."reviews" TO "anon";
GRANT ALL ON TABLE "public"."reviews" TO "authenticated";
GRANT ALL ON TABLE "public"."reviews" TO "service_role";



GRANT ALL ON SEQUENCE "public"."reviews_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."reviews_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."reviews_id_seq" TO "service_role";



GRANT ALL ON TABLE "public"."scraped_prices" TO "anon";
GRANT ALL ON TABLE "public"."scraped_prices" TO "authenticated";
GRANT ALL ON TABLE "public"."scraped_prices" TO "service_role";



GRANT ALL ON SEQUENCE "public"."scraped_prices_id_seq" TO "anon";
GRANT ALL ON SEQUENCE "public"."scraped_prices_id_seq" TO "authenticated";
GRANT ALL ON SEQUENCE "public"."scraped_prices_id_seq" TO "service_role";



ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";







