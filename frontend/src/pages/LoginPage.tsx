import { type FormEvent, useState } from "react";
import { Navigate } from "react-router";
import { login } from "../api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const { user, login: setToken, loading: authLoading } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (authLoading) return null;
  if (user) return <Navigate to="/feedback" replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await login(username, password);
      setToken(res.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-stone-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo area */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-stone-900">
            SignalDesk
          </h1>
          <p className="text-sm text-stone-500 mt-1">
            Customer feedback intelligence
          </p>
        </div>

        {/* Card */}
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl border border-stone-200/80 shadow-sm p-6 space-y-4"
        >
          <Input
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
            autoFocus
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-md px-3 py-2">
              {error}
            </p>
          )}

          <Button
            type="submit"
            loading={submitting}
            className="w-full"
          >
            Sign in
          </Button>
        </form>
      </div>
    </div>
  );
}
