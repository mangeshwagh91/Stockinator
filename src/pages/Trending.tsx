import WatchlistPanel from "@/components/WatchlistPanel";
import IndicatorPanel from "@/components/IndicatorPanel";

const Trending = () => (
  <div className="grid grid-cols-12 gap-4 max-w-[1920px] mx-auto">
    <div className="col-span-12 lg:col-span-5">
      <WatchlistPanel />
    </div>
    <div className="col-span-12 lg:col-span-7">
      <IndicatorPanel />
    </div>
  </div>
);

export default Trending;
