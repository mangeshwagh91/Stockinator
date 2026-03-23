type AgentCycleCardProps = {
  title: string;
  description: string;
  tone?: "default" | "positive" | "warning";
};

const toneClass: Record<NonNullable<AgentCycleCardProps["tone"]>, string> = {
  default: "border-white/10 bg-slate-900/60 text-slate-100",
  positive: "border-emerald-500/30 bg-emerald-950/30 text-emerald-100",
  warning: "border-orange-500/30 bg-orange-950/30 text-orange-100",
};

const AgentCycleCard = ({ title, description, tone = "default" }: AgentCycleCardProps) => {
  return (
    <article className={`rounded-xl border p-4 ${toneClass[tone]}`}>
      <h3 className="text-xs font-black tracking-[0.2em] uppercase">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-slate-300">{description}</p>
    </article>
  );
};

export default AgentCycleCard;
