"use client";

import { useState } from "react";
import { supabase, type Review } from "@/lib/supabase";

type Props = {
  clinicId: number;
  onSubmitted: (review: Review) => void;
};

export default function ReviewForm({ clinicId, onSubmitted }: Props) {
  const [rating, setRating] = useState(0);
  const [hovered, setHovered] = useState(0);
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (rating === 0) { setError("Please select a star rating."); return; }
    if (!body.trim()) { setError("Please write a review."); return; }

    setSubmitting(true);
    setError("");

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      setError("You must be signed in to leave a review.");
      setSubmitting(false);
      return;
    }

    const { data, error: err } = await supabase
      .from("reviews")
      .insert({ clinic_id: clinicId, user_id: user.id, rating, body: body.trim() })
      .select()
      .single();

    if (err) {
      setError(err.message);
    } else {
      onSubmitted(data);
      setRating(0);
      setBody("");
      setDone(true);
    }
    setSubmitting(false);
  }

  if (done) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-700">
        Thanks for your review!
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border shadow-sm p-4 space-y-3">
      <h3 className="font-semibold text-gray-900">Leave a review</h3>

      {/* Star picker */}
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setRating(s)}
            onMouseEnter={() => setHovered(s)}
            onMouseLeave={() => setHovered(0)}
            className={`text-2xl transition-colors ${
              s <= (hovered || rating) ? "text-yellow-400" : "text-gray-300"
            }`}
          >
            ★
          </button>
        ))}
      </div>

      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Share your experience..."
        rows={3}
        className="w-full border rounded-lg px-3 py-2 text-sm resize-none"
      />

      {error && <p className="text-red-500 text-xs">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? "Submitting..." : "Submit review"}
      </button>
    </form>
  );
}
