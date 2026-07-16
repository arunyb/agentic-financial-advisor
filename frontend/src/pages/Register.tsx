import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { AuthLayout } from "../components/AuthLayout";
import { AxiosError } from "axios";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(email, fullName, password);
      navigate("/dashboard");
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      setError(axiosErr.response?.data?.detail ?? "Could not create your account.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Set up your advisory desk in under a minute">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-soft">
            Full name
          </label>
          <input
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-line px-3 py-2 text-sm focus:border-indigo"
            placeholder="Jordan Rivera"
          />
        </div>
        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-soft">
            Email
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-line px-3 py-2 text-sm focus:border-indigo"
            placeholder="you@example.com"
          />
        </div>
        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-soft">
            Password
          </label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-line px-3 py-2 text-sm focus:border-indigo"
            placeholder="At least 8 characters"
          />
        </div>

        {error && <p className="text-sm text-amber">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-indigo px-3 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-dark disabled:opacity-60"
        >
          {submitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-soft">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-indigo-dark hover:underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
