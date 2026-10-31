"use client";

import { useEffect, useState } from "react";
import { api, formatMoney, todayIST } from "@/lib/api";
import type { Summary } from "@/lib/types";

export default function DashboardPage() {
  const [month, setMonth] = useState(todayIST().slice(0, 7));
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!/^\d{4}-\d{2}$/.test(month)) return;
    setLoading(true);
    api.summary(month)
      .then((s) => { setSummary(s); setError(null); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [month]);

  const max = summary ? Math.max(...summary.by_category.map((c) => Number(c.total)), 0) : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-xl font-semibold">Monthly summary</h1>
        <div>
          <label className="label" htmlFor="month">Month</label>
          <input id="month" type="month" className="input" value={month} onChange={(e) => setMonth(e.target.value)} />
        </div>
      </div>

      {error && <p className="rounded bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}

      {loading && !summary ? (
        <p className="text-sm text-slate-500">Loading summary…</p>
      ) : summary && (
        <div className={`space-y-4 ${loading ? "opacity-50" : ""}`}>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="card">
              <p className="text-xs uppercase text-slate-500">Total spent</p>
              <p className="mt-1 text-3xl font-semibold tabular-nums">{formatMoney(summary.total)}</p>
            </div>
            <div className="card">
              <p className="text-xs uppercase text-slate-500">Expenses</p>
              <p className="mt-1 text-3xl font-semibold tabular-nums">{summary.count}</p>
            </div>
          </div>

          <div className="card">
            <h2 className="mb-3 font-semibold">By category</h2>
            {summary.by_category.length === 0 ? (
              <p className="text-sm text-slate-500">No expenses recorded for this month.</p>
            ) : (
              <ul className="space-y-3">
                {summary.by_category.map((c) => (
                  <li key={c.category_id}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span>{c.category_name} <span className="text-slate-400">({c.count})</span></span>
                      <span className="font-medium tabular-nums">{formatMoney(c.total)}</span>
                    </div>
                    <div className="h-2 rounded bg-slate-100">
                      <div className="h-2 rounded bg-indigo-500" style={{ width: `${max ? (Number(c.total) / max) * 100 : 0}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
