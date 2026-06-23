import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { IndustriesPage } from "./pages/IndustriesPage";
import { StocksPage } from "./pages/StocksPage";
import { StockDetailPage } from "./pages/StockDetailPage";
import { MacroPage } from "./pages/MacroPage";
import { InstitutionWatchPage } from "./pages/InstitutionWatchPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SettingsPage } from "./pages/SettingsPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/industries" element={<IndustriesPage />} />
        <Route path="/stocks" element={<StocksPage />} />
        <Route path="/stocks/:stockCode" element={<StockDetailPage />} />
        <Route path="/macro" element={<MacroPage />} />
        <Route path="/institution-watch" element={<InstitutionWatchPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
