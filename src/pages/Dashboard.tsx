import WatchlistPanel from "@/components/WatchlistPanel";
import ChartPanel from "@/components/ChartPanel";
import RiskPanel from "@/components/RiskPanel";

const Dashboard = () => (
  <div className="grid grid-cols-12 gap-4 max-w-[1920px] mx-auto">
    <div className="col-span-12 lg:col-span-4">
      <WatchlistPanel />
    </div>
    <div className="col-span-12 lg:col-span-8 space-y-4">
      <ChartPanel />
      <RiskPanel />
    </div>
  </div>
);

export default Dashboard;
