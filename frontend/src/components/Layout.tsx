import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { backendApi } from "@/lib/backendApi";

const Layout = ({ children }: { children: React.ReactNode }) => {
  const [utcTime, setUtcTime] = useState(() =>
    new Date().toLocaleTimeString("en-GB", {
      timeZone: "UTC",
      hour12: false,
    }),
  );

  useEffect(() => {
    const timer = setInterval(() => {
      setUtcTime(
        new Date().toLocaleTimeString("en-GB", {
          timeZone: "UTC",
          hour12: false,
        }),
      );
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const { data: health } = useQuery({
    queryKey: ["backend-health"],
    queryFn: backendApi.getHealth,
    refetchInterval: 20000,
    retry: 1,
  });

  const liveHealthy = health?.status === "healthy";

  return (
    <div className="geo-shell">
      <header className="geo-topbar">
        <div className="geo-brand-block">
          <div className="geo-brand-mark" aria-hidden="true">
            <span />
          </div>
          <div>
            <div className="geo-brand">STOCKINATOR</div>
            <div className="geo-brand-sub">TRADER V2.0</div>
          </div>
          <div className="geo-gti-wrap">
            <span className="geo-gti-label">GLOBAL TENSION INDEX (GTI)</span>
            <div className="geo-gti-value-row">
              <span className="geo-gti-value">71.4</span>
              <span className="geo-gti-delta">^+2.1</span>
              <span className="geo-chip geo-chip-warning">ELEVATED</span>
            </div>
          </div>
        </div>

        <nav className="geo-topnav" aria-label="Primary">
          <TopNavItem label="EARTH PULSE" to="/" />
          <TopNavItem label="GEO MAP" to="/trending" />
          <TopNavItem label="AI SIGNALS" to="/indicators" />
          <TopNavItem label="PORTFOLIO" to="/positions" />
        </nav>

        <div className="geo-meta-block">
          <div className={liveHealthy ? "geo-pill geo-pill-live" : "geo-pill geo-pill-offline"}>
            {liveHealthy ? "LIVE · backend online" : "DEGRADED · backend offline"}
          </div>
          <div className="geo-pill">{utcTime} UTC</div>
        </div>
      </header>

      <main className="geo-main">{children}</main>

      <button className="geo-waitlist" type="button">JOIN WAITLIST</button>
    </div>
  );
};

const TopNavItem = ({ label, to }: { label: string; to: string }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      isActive ? "geo-topnav-item geo-topnav-item-active" : "geo-topnav-item"
    }
    end={to === "/"}
  >
    {label}
  </NavLink>
);

export default Layout;
