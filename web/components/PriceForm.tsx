"use client";

import { useState } from "react";
import { supabase, type PriceReport } from "@/lib/supabase";

const COMMON_TREATMENTS = [
  "Check-up & clean",
  "X-rays",
  "Filling (composite)",
  "Filling (amalgam)",
  "Root canal",
  "Crown",
  "Extraction",
  "Teeth whitening",
  "Implant",
  "Orthodontic consultation",
];

type Props = {
  clinicId: number;
  onSubmitted: (report: PriceReport) => void;
};

export default function PriceForm({ clinicId, onSubmitted }: Props) {
  const [treatment, setTreatment] = useState("");
  const [customTreatment, setCustomTreatment] = useState("");
  const [price, setPrice] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const treatmentName = treatment === "other" ? customTreatment.trim() : treatment;
    if (!treatmentName) { setError("Please select or enter a treatment."); return; }
    if (!price || isNaN(parseInt(price)) || parseInt(price) <= 0) {
      setError("Please enter a valid price in NZD.");
      return;
    }

    setSubmitting(true);
    setError("");

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      setError("You must be signed in to submit a price.");
      setSubmitting(false);
      return;
    }

    const { data, error: err } = await supabase
      .from("price_reports")
      .insert({
        clinic_id: clinicId,
        user_id: user.id,
        treatment: treatmentName,
        price_nzd: parseInt(price),
        notes: notes.trim() || null,
      })
      .select()
      .single();

    if (err) {
      setError(err.message);
    } else {
      onSubmitted(data);
      setTreatment("");
      setPrice("");
      setNotes("");
      setDone(true);
    }
    setSubmitting(false);
  }

  if (done) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-700">
        Thanks for submitting a price!
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border shadow-sm p-4 space-y-3">
      <h3 className="font-semibold text-gray-900">Submit a price</h3>
      <p className="text-xs text-gray-500">Help others by sharing what you paid.</p>

      <select
        value={treatment}
        onChange={(e) => setTreatment(e.target.value)}
        className="w-full border rounded-lg px-3 py-2 text-sm"
      >
        <option value="">Select treatment...</option>
        {COMMON_TREATMENTS.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
        <option value="other">Other...</option>
      </select>

      {treatment === "other" && (
        <input
          type="text"
          placeholder="Treatment name"
          value={customTreatment}
          onChange={(e) => setCustomTreatment(e.target.value)}
          className="w-full border rounded-lg px-3 py-2 text-sm"
        />
      )}

      <div className="flex gap-2 items-center">
        <span className="text-sm text-gray-500">NZD $</span>
        <input
          type="number"
          placeholder="Price"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          min="1"
          className="border rounded-lg px-3 py-2 text-sm w-32"
        />
      </div>

      <input
        type="text"
        placeholder="Notes (optional, e.g. subsidised, ACC)"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        className="w-full border rounded-lg px-3 py-2 text-sm"
      />

      {error && <p className="text-red-500 text-xs">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? "Submitting..." : "Submit price"}
      </button>
    </form>
  );
}
