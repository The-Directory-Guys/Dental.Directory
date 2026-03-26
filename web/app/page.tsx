"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { supabase, type Clinic } from "@/lib/supabase";

const REGIONS = [
  "Auckland",
  "Bay of Plenty",
  "Canterbury",
  "Gisborne",
  "Hawke's Bay",
  "Manawatū-Whanganui",
  "Marlborough",
  "Nelson/Tasman",
  "Northland",
  "Otago",
  "Southland",
  "Taranaki",
  "Waikato",
  "Wellington",
  "West Coast",
];

const PAGE_SIZE = 20;

export default function HomePage() {
  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [region, setRegion] = useState("");
  const [minRating, setMinRating] = useState("");
  const [sortBy, setSortBy] = useState("rating");
  const [page, setPage] = useState(0);

  const fetchClinics = useCallback(async () => {
    setLoading(true);

    let query = supabase
      .from("dental_clinics")
      .select("*", { count: "exact" })
      .eq("business_status", "OPERATIONAL");

    if (search.trim()) {
      query = query.ilike("name", `%${search.trim()}%`);
    }
    if (region) {
      query = query.eq("region", region);
    }
    if (minRating) {
      query = query.gte("rating", parseFloat(minRating));
    }

    if (sortBy === "rating") {
      query = query.order("rating", { ascending: false, nullsFirst: false });
    } else if (sortBy === "reviews") {
      query = query.order("total_ratings", { ascending: false, nullsFirst: false });
    } else {
      query = query.order("name");
    }

    query = query.range(page * PAGE_SIZE, (page + 1) * PAGE_SIZE - 1);

    const { data, count, error } = await query;
    if (!error && data) {
      setClinics(data);
      setTotal(count ?? 0);
    }
    setLoading(false);
  }, [search, region, minRating, sortBy, page]);

  useEffect(() => {
    setPage(0);
  }, [search, region, minRating, sortBy]);

  useEffect(() => {
    fetchClinics();
  }, [fetchClinics]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-5">
          <h1 className="text-2xl font-bold text-blue-700">NZ Dental Directory</h1>
          <p className="text-sm text-gray-500 mt-1">
            Compare dental clinics across New Zealand — read and submit reviews and prices.
          </p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border p-4 mb-6 flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="Search clinic name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm flex-1 min-w-48"
          />

          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm"
          >
            <option value="">All regions</option>
            {REGIONS.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>

          <select
            value={minRating}
            onChange={(e) => setMinRating(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm"
          >
            <option value="">Any rating</option>
            <option value="4.5">4.5+</option>
            <option value="4">4.0+</option>
            <option value="3.5">3.5+</option>
            <option value="3">3.0+</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm"
          >
            <option value="rating">Sort: Rating</option>
            <option value="reviews">Sort: Most reviewed</option>
            <option value="name">Sort: Name A–Z</option>
          </select>
        </div>

        <p className="text-sm text-gray-500 mb-4">
          {loading ? "Loading..." : `${total.toLocaleString()} clinics found`}
        </p>

        {/* Clinic grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {clinics.map((clinic) => (
            <Link
              key={clinic.id}
              href={`/clinics/${clinic.id}`}
              className="bg-white rounded-xl border shadow-sm p-4 hover:shadow-md transition-shadow"
            >
              <h2 className="font-semibold text-gray-900 truncate">{clinic.name}</h2>
              <p className="text-sm text-gray-500 mt-1 truncate">
                {clinic.suburb_town ?? clinic.town ?? clinic.region}
              </p>
              <p className="text-xs text-gray-400 mt-0.5 truncate">{clinic.address}</p>

              <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-1">
                  <span className="text-yellow-400 text-sm">★</span>
                  <span className="text-sm font-medium">
                    {clinic.rating ? clinic.rating.toFixed(1) : "—"}
                  </span>
                  <span className="text-xs text-gray-400">
                    ({clinic.total_ratings?.toLocaleString() ?? 0})
                  </span>
                </div>
                <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                  {clinic.region}
                </span>
              </div>
            </Link>
          ))}
        </div>

        {/* Pagination */}
        {total > PAGE_SIZE && (
          <div className="flex justify-center gap-2 mt-8">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-4 py-2 border rounded-lg text-sm disabled:opacity-40"
            >
              Previous
            </button>
            <span className="px-4 py-2 text-sm text-gray-600">
              Page {page + 1} of {Math.ceil(total / PAGE_SIZE)}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={(page + 1) * PAGE_SIZE >= total}
              className="px-4 py-2 border rounded-lg text-sm disabled:opacity-40"
            >
              Next
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
