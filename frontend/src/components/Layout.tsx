import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { riskMetrics } from "@/data/mockData";

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-12 flex items-center justify-between border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50 px-4">
            <div className="flex items-center gap-3">
              <SidebarTrigger />
              <div className="hidden sm:flex items-center gap-4 text-xs font-mono">
                <TickerItem symbol="NIFTY" value="22,458" change="+0.85%" positive />
                <TickerItem symbol="BTC" value="67,432" change="+1.88%" positive />
                <TickerItem symbol="ETH" value="3,521" change="-1.19%" positive={false} />
              </div>
            </div>
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="text-muted-foreground">
                Capital: <span className="text-foreground font-semibold">₹{(riskMetrics.totalCapital / 100000).toFixed(1)}L</span>
              </span>
              <span className="text-muted-foreground">
                P&L:{" "}
                <span className={riskMetrics.dailyPnL >= 0 ? "text-bullish font-semibold" : "text-bearish font-semibold"}>
                  {riskMetrics.dailyPnL >= 0 ? "+" : ""}₹{riskMetrics.dailyPnL.toLocaleString()}
                </span>
              </span>
            </div>
          </header>
          <main className="flex-1 p-4 overflow-auto">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

const TickerItem = ({ symbol, value, change, positive }: { symbol: string; value: string; change: string; positive: boolean }) => (
  <div className="flex items-center gap-1.5">
    <span className="text-muted-foreground">{symbol}</span>
    <span className="text-foreground font-semibold">{value}</span>
    <span className={positive ? "text-bullish" : "text-bearish"}>{change}</span>
  </div>
);

export default Layout;
