import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "./useAuth";

export function useApi<T>(
  url: string | null,
  deps: unknown[] = [],
): {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
} {
  const { token, logout } = useAuth();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(url !== null);
  const [error, setError] = useState<string | null>(null);
  const seqRef = useRef(0);

  const apiBase =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  const fetchData = useCallback(() => {
    if (!url || !token) {
      setLoading(false);
      return;
    }

    const seq = ++seqRef.current;
    setLoading(true);
    setError(null);

    fetch(`${apiBase}${url}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (seq !== seqRef.current) return;
        if (res.status === 401) {
          logout();
          return;
        }
        if (!res.ok) {
          const body = await res.json().catch(() => null);
          throw new Error(
            (body && typeof body.detail === "string" && body.detail) ||
              `Request failed (${res.status})`,
          );
        }
        const json = (await res.json()) as T;
        setData(json);
      })
      .catch((err: unknown) => {
        if (seq !== seqRef.current) return;
        setError(err instanceof Error ? err.message : "Request failed");
      })
      .finally(() => {
        if (seq === seqRef.current) setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, token, apiBase, logout, ...deps]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
