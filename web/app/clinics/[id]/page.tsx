"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { supabase, type Clinic, type Review, type PriceReport, type ScrapedPrice } from "@/lib/supabase";
import ReviewForm from "@/components/ReviewForm";
import PriceForm from "@/components/PriceForm";

export default function ClinicPage() {
  const { id: idParam } = useParams<{ id: string }>();
  const clinicId = idParam ? parseInt(idParam, 10) : NaN;

  const [clinic, setClinic] = useState<Clinic | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [prices, setPrices] = useState<PriceReport[]>([]);
  const [scrapedPrices, setScrapedPrices] = useState<ScrapedPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"info" | "reviews" | "prices">("info");

  useEffect(() => {
    async function load() {
      if (!Number.isFinite(clinicId)) {
        setLoading(false);
        return;
      }
      const [{ data: c }, { data: r }, { data: p }, { data: sp }] = await Promise.all([
        supabase.from("dental_clinics").select("*").eq("id", clinicId).single(),
        supabase
          .from("reviews")
          .select("*")
          .eq("clinic_id", clinicId)
          .order("created_at", { ascending: false }),
        supabase
          .from("price_reports")
          .select("*")
          .eq("clinic_id", clinicId)
          .order("created_at", { ascending: false }),
        supabase
          .from("scraped_prices")
          .select("*")
          .eq("clinic_id", clinicId)
          .order("treatment", { ascending: true }),
      ]);
      setClinic(c);
      setReviews(r ?? []);
      setPrices(p ?? []);
      setScrapedPrices(sp ?? []);
      setLoading(false);
    }
    load();
  }, [clinicId]);

  if (loading) return <div className="p-8 text-gray-400">Loading...</div>;
  if (!clinic) return <div className="p-8 text-red-500">Clinic not found.</div>;

  const hours = clinic.opening_hours
    ? clinic.opening_hours.split("; ")
    : [];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <Link href="/" className="text-sm text-blue-600 hover:underline">← Back to directory</Link>
          <h1 className="text-xl font-bold text-gray-900 mt-2">{clinic.name}</h1>
          <p className="text-sm text-gray-500">{clinic.address}</p>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6">
        {/* Summary card */}
        <div className="bg-white rounded-xl border shadow-sm p-5 mb-6 flex flex-wrap gap-6">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Rating</p>
            <p className="text-2xl font-bold text-yellow-500">
              {clinic.rating ? `★ ${clinic.rating.toFixed(1)}` : "—"}
            </p>
            <p className="text-xs text-gray-400">{clinic.total_ratings?.toLocaleString()} reviews</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Region</p>
            <p className="font-medium">{clinic.region}</p>
            <p className="text-xs text-gray-400 uppercase tracking-wide mt-2">City</p>
            <p className="text-sm text-gray-500">
              {clinic.city && clinic.city !== "NA" ? clinic.city : "NA"}
            </p>
            <p className="text-xs text-gray-400 uppercase tracking-wide mt-2">
              Suburb / town
            </p>
            <p className="text-sm text-gray-500">
              {clinic.suburb_town ?? clinic.town ?? "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Phone</p>
            <p className="font-medium">{clinic.phone_national ?? clinic.phone_international ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Website</p>
            {clinic.website ? (
              <a href={clinic.website} target="_blank" rel="noopener noreferrer"
                className="text-blue-600 hover:underline text-sm truncate max-w-48 block">
                {clinic.website.replace(/^https?:\/\//, "")}
              </a>
            ) : <p className="text-sm text-gray-400">—</p>}
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Google Maps</p>
            <a href={clinic.google_maps_url} target="_blank" rel="noopener noreferrer"
              className="text-blue-600 hover:underline text-sm">View on Maps</a>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b">
          {(["info", "reviews", "prices"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium capitalize border-b-2 -mb-px transition-colors ${
                activeTab === tab
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab === "reviews" ? `Reviews (${reviews.length})` :
               tab === "prices" ? `Prices (${prices.length})` : "Info"}
            </button>
          ))}
        </div>

        {/* Info tab */}
        {activeTab === "info" && (
          <div className="bg-white rounded-xl border shadow-sm p-5">
            <h2 className="font-semibold mb-3">Opening Hours</h2>
            {hours.length > 0 ? (
              <ul className="text-sm space-y-1">
                {hours.map((h, i) => (
                  <li key={i} className="text-gray-600">{h}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">No hours available.</p>
            )}
          </div>
        )}

        {/* Reviews tab */}
        {activeTab === "reviews" && (
          <div className="space-y-4">
            <ReviewForm
              clinicId={clinicId}
              onSubmitted={(r) => setReviews([r, ...reviews])}
            />
            {reviews.length === 0 ? (
              <p className="text-sm text-gray-400">No reviews yet. Be the first!</p>
            ) : (
              reviews.map((r) => (
                <div key={r.id} className="bg-white rounded-xl border shadow-sm p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-yellow-400">{"★".repeat(r.rating)}{"☆".repeat(5 - r.rating)}</span>
                    <span className="text-xs text-gray-400">{new Date(r.created_at).toLocaleDateString("en-NZ")}</span>
                  </div>
                  <p className="text-sm text-gray-700">{r.body}</p>
                </div>
              ))
            )}
          </div>
        )}

        {/* Prices tab */}
        {activeTab === "prices" && (
          <div className="space-y-6">
            {/* Scraped prices */}
            {scrapedPrices.length > 0 && (
              <div>
                <div className="flex items-baseline justify-between mb-2">
                  <h2 className="font-semibold text-gray-800">Pricing &amp; Payment Information</h2>
                  {clinic.prices_last_updated && (
                    <span className="text-xs text-gray-400">
                      Last updated {new Date(clinic.prices_last_updated).toLocaleDateString("en-NZ", { day: "numeric", month: "long", year: "numeric" })}
                    </span>
                  )}
                </div>
                <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left px-4 py-2 font-medium text-gray-600">Treatment / Scheme</th>
                        <th className="text-right px-4 py-2 font-medium text-gray-600">Price (NZD)</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-600">Notes</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {scrapedPrices.map((sp) => (
                        <tr key={sp.id}>
                          <td className="px-4 py-2 text-gray-900">{sp.treatment}</td>
                          <td className="px-4 py-2 text-right font-medium">
                            {sp.price_label ? sp.price_label : sp.price_nzd ? `$${sp.price_nzd}` : "—"}
                          </td>
                          <td className="px-4 py-2 text-gray-500">{sp.notes ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* User-submitted prices */}
            <div>
              <h2 className="font-semibold text-gray-800 mb-2">Community Price Reports</h2>
              <PriceForm
                clinicId={clinicId}
                onSubmitted={(p) => setPrices([p, ...prices])}
              />
              {prices.length === 0 ? (
                <p className="text-sm text-gray-400 mt-3">No prices submitted yet. Be the first!</p>
              ) : (
                <div className="bg-white rounded-xl border shadow-sm overflow-hidden mt-3">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left px-4 py-2 font-medium text-gray-600">Treatment</th>
                        <th className="text-right px-4 py-2 font-medium text-gray-600">Price (NZD)</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-600">Notes</th>
                        <th className="text-right px-4 py-2 font-medium text-gray-600">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {prices.map((p) => (
                        <tr key={p.id}>
                          <td className="px-4 py-2 text-gray-900">{p.treatment}</td>
                          <td className="px-4 py-2 text-right font-medium">${p.price_nzd}</td>
                          <td className="px-4 py-2 text-gray-500">{p.notes ?? "—"}</td>
                          <td className="px-4 py-2 text-right text-gray-400">
                            {new Date(p.created_at).toLocaleDateString("en-NZ")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
