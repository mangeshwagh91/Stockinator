import { useMemo } from "react";
import { useMutation } from "@tanstack/react-query";
import AgentCycleCard from "@/features/dashboard/components/AgentCycleCard";
import { useSystemWorkflow } from "@/features/dashboard/hooks/useSystemWorkflow";
import { backendApi } from "@/lib/backendApi";

const SystemControl = () => {
  const workflow = useSystemWorkflow();

  const decisionMutation = useMutation({
    mutationFn: backendApi.evaluateDecision,
  });

  const cycleSteps = workflow.data?.cycle ?? [];

  const demoPayload = useMemo(
    () => ({
      symbol: "BANKNIFTY",
      last_price: 49215,
      bullish_patterns: 4,
      bearish_patterns: 1,
      xgboost_probability: 84,
      news_sentiment: 68,
      expected_profit: 220,
      cost_estimate: 55,
      daily_pnl: 1200,
      open_positions: 2,
      cooldown_elapsed: true,
      position_size_within_limits: true,
    }),
    [],
  );

  return (
    <main className="min-h-screen bg-[#05070a] text-slate-100 p-6 md:p-10">
      <header className="max-w-6xl mx-auto">
        <h1 className="text-3xl md:text-4xl font-black tracking-tight">System Control</h1>
        <p className="mt-3 text-slate-400 max-w-3xl">
          Operational control center for the multi-agent trading cycle with transparent decisioning and risk-first automation.
        </p>
      </header>

      <section className="max-w-6xl mx-auto mt-8 grid grid-cols-1 lg:grid-cols-3 gap-4">
        {cycleSteps.map((step, index) => (
          <AgentCycleCard
            key={step}
            title={`Step ${index + 1}`}
            description={step.replace(/_/g, " ")}
            tone={index === 0 ? "positive" : index === cycleSteps.length - 1 ? "warning" : "default"}
          />
        ))}
      </section>

      <section className="max-w-6xl mx-auto mt-10 rounded-2xl border border-white/10 bg-slate-900/40 p-6">
        <h2 className="text-sm uppercase tracking-[0.2em] text-slate-400">Decision Simulator</h2>
        <p className="mt-2 text-sm text-slate-500">Runs the same orchestrator gate used by backend agents.</p>

        <button
          type="button"
          onClick={() => decisionMutation.mutate(demoPayload)}
          className="mt-4 rounded-md bg-emerald-500/90 px-5 py-2 text-xs font-black tracking-[0.2em] uppercase text-black hover:bg-emerald-400"
        >
          Simulate Decision
        </button>

        {decisionMutation.data && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="rounded-lg border border-white/10 bg-black/30 p-4">
              <div className="text-slate-400 uppercase text-[10px] tracking-[0.2em]">Success Score</div>
              <div className="mt-2 text-2xl font-black">{decisionMutation.data.prediction.success_score.toFixed(1)}%</div>
            </div>
            <div className="rounded-lg border border-white/10 bg-black/30 p-4">
              <div className="text-slate-400 uppercase text-[10px] tracking-[0.2em]">Action</div>
              <div className="mt-2 text-2xl font-black">{decisionMutation.data.decision.action}</div>
            </div>
            <div className="rounded-lg border border-white/10 bg-black/30 p-4">
              <div className="text-slate-400 uppercase text-[10px] tracking-[0.2em]">Reason</div>
              <div className="mt-2 text-sm text-slate-300">{decisionMutation.data.decision.reason}</div>
            </div>
          </div>
        )}
      </section>
    </main>
  );
};

export default SystemControl;
