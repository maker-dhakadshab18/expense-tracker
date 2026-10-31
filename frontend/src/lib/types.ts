// Mirrors backend/app/schemas.py. Money comes back as a decimal string (e.g. "250.50").

export type Category = { id: number; name: string };

export type Expense = {
  id: number;
  amount: string;
  expense_date: string; // YYYY-MM-DD
  note: string | null;
  category: Category;
  created_at: string;
  updated_at: string;
};

export type ExpensePage = {
  items: Expense[];
  total: number;
  page: number;
  page_size: number;
};

export type ExpenseInput = {
  amount: string;
  expense_date: string;
  category_id: number;
  note: string | null;
};

export type Summary = {
  month: string;
  total: string;
  count: number;
  by_category: { category_id: number; category_name: string; total: string; count: number }[];
};

export type User = { id: number; email: string; created_at: string };
