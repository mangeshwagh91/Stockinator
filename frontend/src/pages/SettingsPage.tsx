const SettingsPage = () => (
  <div className="max-w-2xl mx-auto space-y-6">
    <div>
      <h1 className="text-xl font-mono font-bold text-foreground">Settings</h1>
      <p className="text-sm text-muted-foreground mt-1">Configure trading parameters and system preferences.</p>
    </div>
    <div className="rounded-lg border border-border bg-card p-6 space-y-4">
      <SettingRow label="Brokerage Cost" value="₹50 per trade" />
      <SettingRow label="Score Threshold" value="80%" />
      <SettingRow label="Cooldown Period" value="30 minutes" />
      <SettingRow label="Max Daily Loss" value="2% of capital" />
      <SettingRow label="Max Positions" value="5" />
      <SettingRow label="Stop-Loss" value="1% per trade" />
    </div>
  </div>
);

const SettingRow = ({ label, value }: { label: string; value: string }) => (
  <div className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
    <span className="text-sm text-muted-foreground">{label}</span>
    <span className="text-sm font-mono text-foreground font-medium">{value}</span>
  </div>
);

export default SettingsPage;
