import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import { initWasm } from "./lib/wasm";

async function bootstrap() {
  await initWasm();

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register("/sw.js")
        .catch((error) => console.warn("Service worker registration failed:", error));
    });
  }

  const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

bootstrap();

