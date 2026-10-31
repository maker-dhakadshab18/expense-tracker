import type { Category, Expense, ExpenseInput, ExpensePage, Summary, User } from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const TOKEN_KEY = "token";

export const auth = {
  get: () => (typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY)),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

// FastAPI errors: {detail: "msg"} or {detail: [{loc, msg}, ...]} for 422s.
function errorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: (string | number)[]; msg?: string }) => {
        const field = d.loc?.filter((p) => p !== "body").join(".");
        return field ? `${field}: ${d.msg}` : d.msg;
      })
      .join("; ");
  }
  return `Request failed (${status})`;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = auth.get();
  if (token) headers.Authorization = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers: { ...headers, ...init.headers } });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }

  if (res.status === 401 && token) {
    auth.clear();
    window.location.href = "/login";
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, errorMessage(body, res.status));
  return body as T;
}

const json = (method: string, data: unknown): RequestInit => ({ method, body: JSON.stringify(data) });

export const api = {
  register: (email: string, password: string) =>
    request<{ access_token: string }>("/api/v1/auth/register", json("POST", { email, password })),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/api/v1/auth/login", json("POST", { email, password })),
  me: () => request<User>("/api/v1/auth/me"),

  categories: () => request<Category[]>("/api/v1/categories"),
  createCategory: (name: string) => request<Category>("/api/v1/categories", json("POST", { name })),

  expenses: (params: { from?: string; to?: string; category_id?: string; page: number; page_size: number }) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && v !== "" && q.set(k, String(v)));
    return request<ExpensePage>(`/api/v1/expenses?${q}`);
  },
  createExpense: (data: ExpenseInput) => request<Expense>("/api/v1/expenses", json("POST", data)),
  updateExpense: (id: number, data: Partial<ExpenseInput>) =>
    request<Expense>(`/api/v1/expenses/${id}`, json("PATCH", data)),
  deleteExpense: (id: number) => request<void>(`/api/v1/expenses/${id}`, { method: "DELETE" }),

  summary: (month: string) => request<Summary>(`/api/v1/summary?month=${month}`),
};

const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" });
export const formatMoney = (amount: string) => inr.format(Number(amount));

// "Today" in IST as YYYY-MM-DD, regardless of the device's timezone.
export const todayIST = () => new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });
