"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LiveStat } from "@/lib/api";

interface StatsPanelProps {
  stats: LiveStat | null;
  homeTeam: string;
  awayTeam: string;
}

function StatRow({ label, home, away }: { label: string; home: string | number; away: string | number }) {
  return (
    <div className="grid grid-cols-3 items-center gap-2 py-1.5 text-sm">
      <span className="text-right font-medium tabular-nums">{home}</span>
      <span className="text-center text-xs text-muted-foreground">{label}</span>
      <span className="font-medium tabular-nums">{away}</span>
    </div>
  );
}

export function StatsPanel({ stats, homeTeam, awayTeam }: StatsPanelProps) {
  if (!stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Estatísticas</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="py-4 text-center text-sm text-muted-foreground">Sem dados disponíveis</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Estatísticas ao Vivo</CardTitle>
        <div className="grid grid-cols-3 text-xs text-muted-foreground">
          <span className="text-right truncate">{homeTeam}</span>
          <span />
          <span className="truncate">{awayTeam}</span>
        </div>
      </CardHeader>
      <CardContent className="divide-y divide-border">
        <StatRow label="Posse" home={`${stats.possession_home?.toFixed(0) ?? 0}%`} away={`${stats.possession_away?.toFixed(0) ?? 0}%`} />
        <StatRow label="Chutes" home={stats.shots_home} away={stats.shots_away} />
        <StatRow label="No Alvo" home={stats.shots_on_target_home} away={stats.shots_on_target_away} />
        <StatRow label="xG" home={stats.xg_home.toFixed(2)} away={stats.xg_away.toFixed(2)} />
        <StatRow label="Escanteios" home={stats.corners_home} away={stats.corners_away} />
        <StatRow label="Pressão" home={stats.offensive_pressure_home.toFixed(0)} away={stats.offensive_pressure_away.toFixed(0)} />
        <StatRow label="Momentum" home={stats.momentum_home.toFixed(0)} away={stats.momentum_away.toFixed(0)} />
      </CardContent>
    </Card>
  );
}
