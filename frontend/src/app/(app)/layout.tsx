"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, auth } from "@/lib/api";

// Client-side guard: the token lives in localStorage, so the server can't check it.
export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    if (!auth.get()) {
      router.replace("/login");
      return;
    }
    api.me().then((u) => setEmail(u.email)).catch(() => {});
  }, [router]);

  function logout() {
    auth.clear();
    router.replace("/login");
  }

  if (!email) {
    return <div className="flex flex-1 items-center justify-center text-sm text-slate-500">Loading…</div>;
  }

  const nav = [
    { href: "/expenses", label: "Expenses" },
    { href: "/dashboard", label: "Dashboard" },
  ];

  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-4 px-4 py-3">
          <span className="font-semibold">💰 Expenses</span>
          <nav className="flex gap-1">
            {nav.map((n) => (
              <Link key={n.href} href={n.href}
                className={`rounded px-3 py-1.5 text-sm ${pathname === n.href ? "bg-indigo-50 font-medium text-indigo-700" : "text-slate-600 hover:bg-slate-100"}`}>
                {n.label}
              </Link>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm">
            <span className="hidden text-slate-500 sm:inline">{email}</span>
            <button onClick={logout} className="btn-secondary px-3 py-1.5">Log out</button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 p-4">{children}</main>
    </div>
  );
}
