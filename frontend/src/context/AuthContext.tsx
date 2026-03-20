import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getMe } from "../api";
import type { User } from "../types";

interface AuthState {
  token: string | null;
  user: User | null;
  login: (token: string) => void;
  logout: () => void;
  isAdmin: boolean;
  loading: boolean;
}

export const AuthContext = createContext<AuthState | null>(null);

const TOKEN_KEY = "signaldesk_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY),
  );
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(!!localStorage.getItem(TOKEN_KEY));

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const loginFn = useCallback((newToken: string) => {
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
  }, []);

  // Validate token on mount or when token changes
  useEffect(() => {
    if (!token) {
      setLoading(false);
      setUser(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    getMe(token)
      .then((data) => {
        if (cancelled) return;
        setUser({
          id: data.id,
          username: data.username,
          role: data.role as User["role"],
          created_at: data.created_at,
        });
      })
      .catch(() => {
        if (cancelled) return;
        // Token invalid/expired — clear it
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  const value = useMemo<AuthState>(
    () => ({
      token,
      user,
      login: loginFn,
      logout,
      isAdmin: user?.role === "admin",
      loading,
    }),
    [token, user, loginFn, logout, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
