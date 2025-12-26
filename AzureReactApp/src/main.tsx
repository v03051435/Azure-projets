import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { loadAppConfig } from "../public/config/runtimeConfig";

async function bootstrap() {
  await loadAppConfig();

  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
}

bootstrap().catch((err) => {
  console.error(err);
  document.body.innerHTML = `<pre style="padding:16px;color:#b00020">Runtime config load failed:\n${String(
    err
  )}</pre>`;
});
