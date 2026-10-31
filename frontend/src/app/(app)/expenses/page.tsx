"use client";

import { useCallback, useEffect, useState } from "react";
import ExpenseForm from "@/components/ExpenseForm";
import { api, formatMoney } from "@/lib/api";
import type { Category, Expense, ExpensePage } from "@/lib/types";

const PAGE_SIZE = 20;

export default function ExpensesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [data, setData] = useState<ExpensePage | null>(null);
  const [filters, setFilters] = useState({ from: "", to: "", category_id: "" });
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Expense | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await api.expenses({ ...filters, page, page_size: PAGE_SIZE }));
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    api.categories().then(setCategories).catch((err) => setError(err.message));
  }, []);
  useEffect(() => {
    load();
  }, [load]);

  function setFilter(key: keyof typeof filters, value: string) {
    setFilters((f) => ({ ...f, [key]: value }));
    setPage(1);
  }

  async function remove(id: number) {
    try {
      await api.deleteExpense(id);
      setConfirmDelete(null);
      if (data && data.items.length === 1 && page > 1) setPage(page - 1);
      else load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const addCategory = (c: Category) =>
    setCategories((cs) => [...cs, c].sort((a, b) => a.name.localeCompare(b.name)));
  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  const hasFilters = filters.from || filters.to || filters.category_id;

  return (
    <div className="space-y-4">
      <section className="card">
        <h2 className="mb-3 font-semibold">Add expense</h2>
        {categories.length > 0 && (
          <ExpenseForm categories={categories} onSaved={load} onCategoryAdded={addCategory} />
        )}
      </section>

      <section className="card">
        <div className="grid gap-3 sm:grid-cols-4">
          <div>
            <label className="label" htmlFor="f-from">From</label>
            <input id="f-from" type="date" className="input" value={filters.from} onChange={(e) => setFilter("from", e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="f-to">To</label>
            <input id="f-to" type="date" className="input" value={filters.to} onChange={(e) => setFilter("to", e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="f-cat">Category</label>
            <select id="f-cat" className="input" value={filters.category_id} onChange={(e) => setFilter("category_id", e.target.value)}>
              <option value="">All categories</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="flex items-end">
            <button className="btn-secondary w-full" disabled={!hasFilters}
              onClick={() => { setFilters({ from: "", to: "", category_id: "" }); setPage(1); }}>
              Clear filters
            </button>
          </div>
        </div>
      </section>

      {error && <p className="rounded bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}

      <section className="card overflow-x-auto p-0">
        {loading && !data ? (
          <p className="p-6 text-center text-sm text-slate-500">Loading expenses…</p>
        ) : data && data.items.length === 0 ? (
          <p className="p-6 text-center text-sm text-slate-500">
            {hasFilters ? "No expenses match these filters." : "No expenses yet — add your first one above."}
          </p>
        ) : (
          <table className="w-full min-w-[600px] text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-2">Date</th>
                <th className="px-4 py-2">Category</th>
                <th className="px-4 py-2">Note</th>
                <th className="px-4 py-2 text-right">Amount</th>
                <th className="px-4 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className={loading ? "opacity-50" : ""}>
              {data?.items.map((e) =>
                editing?.id === e.id ? (
                  <tr key={e.id} className="border-b border-slate-100 bg-indigo-50/40">
                    <td colSpan={5} className="p-3">
                      <ExpenseForm categories={categories} initial={e} onCategoryAdded={addCategory}
                        onCancel={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />
                    </td>
                  </tr>
                ) : (
                  <tr key={e.id} className="border-b border-slate-100 last:border-0">
                    <td className="whitespace-nowrap px-4 py-2">{e.expense_date}</td>
                    <td className="px-4 py-2">{e.category.name}</td>
                    <td className="max-w-xs truncate px-4 py-2 text-slate-600">{e.note}</td>
                    <td className="whitespace-nowrap px-4 py-2 text-right font-medium tabular-nums">{formatMoney(e.amount)}</td>
                    <td className="whitespace-nowrap px-4 py-2 text-right">
                      {confirmDelete === e.id ? (
                        <>
                          <span className="mr-2 text-xs text-slate-600">Delete?</span>
                          <button className="mr-2 text-red-600 hover:underline" onClick={() => remove(e.id)}>Yes</button>
                          <button className="text-slate-600 hover:underline" onClick={() => setConfirmDelete(null)}>No</button>
                        </>
                      ) : (
                        <>
                          <button className="mr-3 text-indigo-600 hover:underline" onClick={() => setEditing(e)}>Edit</button>
                          <button className="text-red-600 hover:underline" onClick={() => setConfirmDelete(e.id)}>Delete</button>
                        </>
                      )}
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        )}
      </section>

      {data && data.total > 0 && (
        <div className="flex items-center justify-between text-sm text-slate-600">
          <span>{data.total} expense{data.total === 1 ? "" : "s"}</span>
          <div className="flex items-center gap-2">
            <button className="btn-secondary px-3 py-1" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
            <span>Page {page} of {totalPages}</span>
            <button className="btn-secondary px-3 py-1" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
