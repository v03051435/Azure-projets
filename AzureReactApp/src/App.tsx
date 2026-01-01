import { useEffect, useMemo, useState } from "react";
import { api2BaseUrl, apiBaseUrl, viteEnv } from "../public/config/runtimeConfig";

type Item = {
  id: number;
  name: string;
  description: string;
};

type StatusTone = "emerald" | "amber" | "rose";

function statusLabel(loading: boolean, error: string | null): { label: string; tone: StatusTone } {
  if (loading) return { label: "Syncing", tone: "amber" };
  if (error) return { label: "Degraded", tone: "rose" };
  return { label: "Healthy", tone: "emerald" };
}

function formatTime(value: string | null) {
  return value ?? "Not updated yet";
}

function App() {
  const [items, setItems] = useState<Item[]>([]);
  const [items2, setItems2] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [loading2, setLoading2] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [error2, setError2] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [updatedAt2, setUpdatedAt2] = useState<string | null>(null);
  const API_BASE_URL = apiBaseUrl();
  const API2_BASE_URL = api2BaseUrl();
  const VITE_ENV = viteEnv();

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log(`Fetching data from ${API_BASE_URL}/data`);
        const res = await fetch(`${API_BASE_URL}/data`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`);
        const data = await res.json();
        setItems(data ?? []);
        setUpdatedAt(new Date().toLocaleTimeString());
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") setError(err.message ?? String(err));
        else if (!(err instanceof Error) || err.name !== "AbortError") setError(String(err));
      } finally {
        setLoading(false);
      }
    };
    load();
    return () => controller.abort();
  }, [API_BASE_URL]);

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      try {
        setLoading2(true);
        setError2(null);
        console.log(`Fetching data from ${API2_BASE_URL}/data2`);
        const res = await fetch(`${API2_BASE_URL}/data2`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`Request failed: ${res.status} ${res.statusText}`);
        const data = await res.json();
        setItems2(data ?? []);
        setUpdatedAt2(new Date().toLocaleTimeString());
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== "AbortError") setError2(err.message ?? String(err));
        else if (!(err instanceof Error) || err.name !== "AbortError") setError2(String(err));
      } finally {
        setLoading2(false);
      }
    };
    load();
    return () => controller.abort();
  }, [API2_BASE_URL]);

  const statusApi1 = useMemo(() => statusLabel(loading, error), [loading, error]);
  const statusApi2 = useMemo(() => statusLabel(loading2, error2), [loading2, error2]);

  return (
    <div className="min-h-screen px-6 py-10 lg:px-14">
      <div className="mx-auto flex max-w-6xl flex-col gap-10">
        <header className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
              Repos Observability Console!!!
            </p>
            <h1 className="font-display mt-4 text-4xl font-semibold text-slate-900 sm:text-5xl">
              Unified frontend view for two service APIs.
            </h1>
            <p className="mt-4 text-base text-slate-600">
              This dashboard keeps the UI lightweight while streaming data from both backend
              services. Switch environments without rebuilding the app.
            </p>
          </div>

          <div className="glass-panel relative overflow-hidden rounded-2xl p-6 shadow-glow">
            <div className="absolute -right-6 -top-10 h-32 w-32 rounded-full bg-emerald-300/40 blur-3xl" />
            <div className="absolute -bottom-10 left-8 h-28 w-28 rounded-full bg-amber-300/50 blur-3xl" />
            <div className="relative flex flex-col gap-4">
              <div className="text-xs uppercase tracking-[0.3em] text-slate-500">Environment</div>
              <div className="flex items-center gap-3">
                <span className="status-dot bg-emerald-500" />
                <div>
                  <div className="text-lg font-semibold text-slate-900">{VITE_ENV}</div>
                  <div className="text-xs text-slate-500">Runtime config loaded</div>
                </div>
              </div>
              <div className="text-xs text-slate-500">
                API1: {API_BASE_URL} <br />
                API2: {API2_BASE_URL}
              </div>
            </div>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="glass-panel rounded-2xl p-6 shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Primary API</h2>
                <p className="text-sm text-slate-500">Endpoint: /data</p>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white ${
                  statusApi1.tone === "emerald"
                    ? "bg-emerald-500"
                    : statusApi1.tone === "amber"
                    ? "bg-amber-500"
                    : "bg-rose-500"
                }`}
              >
                {statusApi1.label}
              </span>
            </div>

            <div className="mt-4 text-xs text-slate-500">Last update: {formatTime(updatedAt)}</div>

            {loading && <p className="mt-6 text-sm text-slate-600">Loading records...</p>}
            {error && <p className="mt-6 text-sm text-rose-600">Error: {error}</p>}

            {!loading && !error && items.length === 0 && (
              <p className="mt-6 text-sm text-slate-500">No items found.</p>
            )}

            {!loading && !error && items.length > 0 && (
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-xl border border-slate-200/70 bg-white/80 p-4 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
                  >
                    <h3 className="text-base font-semibold text-slate-900">{item.name}</h3>
                    <p className="mt-2 text-sm text-slate-600">{item.description}</p>
                    <div className="mt-4 text-xs text-slate-400">ID: {item.id}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="glass-panel rounded-2xl p-6 shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Secondary API</h2>
                <p className="text-sm text-slate-500">Endpoint: /data2</p>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white ${
                  statusApi2.tone === "emerald"
                    ? "bg-emerald-500"
                    : statusApi2.tone === "amber"
                    ? "bg-amber-500"
                    : "bg-rose-500"
                }`}
              >
                {statusApi2.label}
              </span>
            </div>

            <div className="mt-4 text-xs text-slate-500">Last update: {formatTime(updatedAt2)}</div>

            {loading2 && <p className="mt-6 text-sm text-slate-600">Loading records...</p>}
            {error2 && <p className="mt-6 text-sm text-rose-600">Error: {error2}</p>}

            {!loading2 && !error2 && items2.length === 0 && (
              <p className="mt-6 text-sm text-slate-500">No items found.</p>
            )}

            {!loading2 && !error2 && items2.length > 0 && (
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {items2.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-xl border border-slate-200/70 bg-white/80 p-4 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
                  >
                    <h3 className="text-base font-semibold text-slate-900">{item.name}</h3>
                    <p className="mt-2 text-sm text-slate-600">{item.description}</p>
                    <div className="mt-4 text-xs text-slate-400">ID: {item.id}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
