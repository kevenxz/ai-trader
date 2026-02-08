import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import Dashboard from "@/pages/Dashboard";
import SchedulerManager from "@/pages/SchedulerManager";
import AI from "@/pages/AI";
import TradingOrders from "@/pages/TradingOrders";

import { ThemeProvider } from "@/components/theme-provider";

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<TradingOrders />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="scheduler" element={<SchedulerManager />} />
            <Route path="ai" element={<AI />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
