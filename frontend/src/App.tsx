import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./App.css";
import GeotradeDashboard from "@/components/GeotradeDashboard";
import AISignalsPage from "@/components/AISignalsPage";
import Trending from "@/pages/Trending";
import Positions from "@/pages/Positions";
import News from "@/pages/News";
import Indicators from "@/pages/Indicators";
import Risk from "@/pages/Risk";
import SettingsPage from "@/pages/SettingsPage";
import TradeLog from "@/pages/TradeLog";
import SystemControl from "@/pages/SystemControl";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<GeotradeDashboard />} />
          <Route path="/signals" element={<AISignalsPage />} />
          <Route path="/trending" element={<Trending />} />
          <Route path="/positions" element={<Positions />} />
          <Route path="/news" element={<News />} />
          <Route path="/history" element={<TradeLog />} />
          <Route path="/indicators" element={<Indicators />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/system" element={<SystemControl />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
