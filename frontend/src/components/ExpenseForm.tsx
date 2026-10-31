"use client";

import { useState } from "react";
import { api, todayIST } from "@/lib/api";
import type { Category, Expense, ExpenseInput } from "@/lib/types";

type Props = {
  categories: Category[];
  initial?: Expense;
  onSaved: () => void;
  onCancel?: () => void;
  onCategoryAdded: (c: Category) => void;
};

const AMOUNT_RE = /^\d{1,10}(\.\d{1,2})?$/;

export default function ExpenseForm({ categories, initial, onSaved, onCancel, onCategoryAdded }: Props) {
  const [amount, setAmount] = useState(initial?.amount ?? "");
  const [date, setDate] = useState(initial?.expense_date ?? todayIST());
  const [categoryId, setCategoryId] = useState(String(initial?.category.id ?? categories[0]?.id ?? ""));
  const [note, setNote] = useState(initial?.note ?? "");
  const [newCat, setNewCat] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function validate(): string | null {
    if (!AMOUNT_RE.test(amount.trim()) || Number(amount) <= 0)
      return "Amount must be a positive number with at most 2 decimal places.";
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return "Please pick a valid date.";
    if (!categoryId) return "Please choose a category.";
    if (note.length > 255) return "Note must be 255 characters or fewer.";
    return null;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const v = validate();
    if (v) return setError(v);
    setError(null);
    setBusy(true);
    const data: ExpenseInput = {
      amount: amount.trim(),
      expense_date: date,
      category_id: Number(categoryId),
      note: note.trim() || null,
    };
    try {
      if (initial) await api.updateExpense(initial.id, data);
      else await api.createExpense(data);
      if (!initial) {
        setAmount("");
        setNote("");
      }
      onSaved();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function addCategory() {
    if (!newCat?.trim()) return;
    try {
      const c = await api.createCategory(newCat.trim());
      onCategoryAdded(c);
      setCategoryId(String(c.id));
      setNewCat(null);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <form onSubmit={onSubmit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5" noValidate>
      <div>
        <label className="label" htmlFor="amount">Amount (₹)</label>
        <input id="amount" inputMode="decimal" className="input" placeholder="0.00"
          value={amount} onChange={(e) => setAmount(e.target.value)} />
      </div>
      <div>
        <label className="label" htmlFor="date">Date</label>
        <input id="date" type="date" className="input" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>
      <div>
        <label className="label" htmlFor="category">Category</label>
        {newCat === null ? (
          <div className="flex gap-1">
            <select id="category" className="input" value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <button type="button" className="btn-secondary px-2" title="New category" onClick={() => setNewCat("")}>+</button>
          </div>
        ) : (
          <div className="flex gap-1">
            <input className="input" placeholder="New category" maxLength={50} autoFocus value={newCat}
              onChange={(e) => setNewCat(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCategory())} />
            <button type="button" className="btn px-2" onClick={addCategory}>Add</button>
            <button type="button" className="btn-secondary px-2" onClick={() => setNewCat(null)}>✕</button>
          </div>
        )}
      </div>
      <div>
        <label className="label" htmlFor="note">Note (optional)</label>
        <input id="note" className="input" maxLength={255} value={note} onChange={(e) => setNote(e.target.value)} />
      </div>
      <div className="flex items-end gap-2">
        <button className="btn flex-1" disabled={busy}>{busy ? "Saving…" : initial ? "Save" : "Add expense"}</button>
        {onCancel && <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>}
      </div>
      {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700 sm:col-span-2 lg:col-span-5" role="alert">{error}</p>}
    </form>
  );
}
