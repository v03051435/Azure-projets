export type AppConfig = {
  API_BASE_URL: string;
  API2_BASE_URL: string;
  VITE_ENV?: string;
};

declare global {
  interface Window {
    __APP_CONFIG__?: AppConfig;
  }
}

export async function loadAppConfig(): Promise<AppConfig> {
  // 必须用相对路径，确保同一镜像在 test/prod 都能工作
  if (import.meta.env.DEV) {
    const localRes = await fetch("/config/config.local.json", { cache: "no-store" });
    if (localRes.ok) {
      const localCfg = (await localRes.json()) as AppConfig;
      window.__APP_CONFIG__ = localCfg;
      return localCfg;
    }
  }
  const res = await fetch("/config/config.json", { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to load /config/config.json (${res.status})`);
  }
  const cfg = (await res.json()) as AppConfig;

  if (!cfg.API_BASE_URL || typeof cfg.API_BASE_URL !== "string") {
    throw new Error("API_BASE_URL missing in config.json");
  }
  if (!cfg.API2_BASE_URL || typeof cfg.API2_BASE_URL !== "string") {
    throw new Error("API2_BASE_URL missing in config.json");
  }

  window.__APP_CONFIG__ = cfg;
  return cfg;
}

export function apiBaseUrl(): string {
  const v = window.__APP_CONFIG__?.API_BASE_URL;
  if (!v) throw new Error("App config not loaded yet");
  return v.replace(/\/$/, "");
}
export function api2BaseUrl(): string {
  const v = window.__APP_CONFIG__?.API2_BASE_URL;
  if (!v) throw new Error("App config not loaded yet");
  return v.replace(/\/$/, "");
}
export function viteEnv(): string {
  const v = window.__APP_CONFIG__?.VITE_ENV;
  if (!v) throw new Error("App config not loaded yet");
  return v;
}
