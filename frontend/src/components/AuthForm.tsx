"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, auth } from "@/lib/api";

export default function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const isRegister = mode === "register";

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (isRegister && password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      const { access_token } = isRegister ? await api.register(email, password) : await api.login(email, password);
      auth.set(access_token);
      router.replace("/expenses");
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center p-4">
      <form onSubmit={onSubmit} className="card w-full max-w-sm space-y-4">
        <h1 className="text-xl font-semibold">{isRegister ? "Create an account" : "Log in"}</h1>
        <div>
          <label className="label" htmlFor="email">Email</label>
          <input id="email" type="email" required className="input" value={email}
            onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input id="password" type="password" required className="input" value={password}
            minLength={isRegister ? 8 : undefined}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={isRegister ? "new-password" : "current-password"} />
          {isRegister && <p className="mt-1 text-xs text-slate-500">At least 8 characters.</p>}
        </div>
        {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700" role="alert">{error}</p>}
        <button className="btn w-full" disabled={busy}>
          {busy ? "Please wait…" : isRegister ? "Sign up" : "Log in"}
        </button>
        <p className="text-center text-sm text-slate-600">
          {isRegister ? "Already have an account? " : "New here? "}
          <Link className="text-indigo-600 hover:underline" href={isRegister ? "/login" : "/register"}>
            {isRegister ? "Log in" : "Create an account"}
          </Link>
        </p>
      </form>
    </main>
  );
}
