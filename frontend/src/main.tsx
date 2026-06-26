import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import App from "./App";
import { AppShell } from "./components/layout/AppShell";
import { ErrorState } from "./components/ui/ErrorState";
import { getSupabaseConfigError } from "./lib/supabase";
import "./styles.css";

const configError = getSupabaseConfigError();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    {configError ? (
      <AppShell>
        <div className="mx-auto max-w-3xl py-8">
          <ErrorState
            title="Supabase 前端設定缺失"
            description={`${configError} GitHub Pages build 也必須注入這兩個值。`}
          />
        </div>
      </AppShell>
    ) : (
      <HashRouter>
        <App />
      </HashRouter>
    )}
  </React.StrictMode>,
);
