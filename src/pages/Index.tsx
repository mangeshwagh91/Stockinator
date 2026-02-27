import Header from "@/components/Header";
import WatchlistPanel from "@/components/WatchlistPanel";
import IndicatorPanel from "@/components/IndicatorPanel";
import NewsFeed from "@/components/NewsFeed";
import PositionsPanel from "@/components/PositionsPanel";
import RiskPanel from "@/components/RiskPanel";
import ChartPanel from "@/components/ChartPanel";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="p-4 grid grid-cols-12 gap-4 max-w-[1920px] mx-auto">
        {/* Left Column - Watchlist & Indicators */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          <WatchlistPanel />
          <IndicatorPanel />
        </div>

        {/* Center Column - Charts & Positions */}
        <div className="col-span-12 lg:col-span-6 space-y-4">
          <ChartPanel />
          <PositionsPanel />
        </div>

        {/* Right Column - News & Risk */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          <RiskPanel />
          <NewsFeed />
        </div>
      </main>
    </div>
  );
};

export default Index;
