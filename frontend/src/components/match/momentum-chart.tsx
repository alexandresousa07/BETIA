"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LiveStat } from "@/lib/api";

interface MomentumChartProps {
  stats: LiveStat[];
}

export function MomentumChart({ stats }: MomentumChartProps) {
  const data = stats.map((s) => ({
    minute: s.minute,
    Mandante: s.momentum_home,
    Visitante: s.momentum_away,
    xG_M: s.xg_home,
    xG_V: s.xg_away,
  }));

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Momentum</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="py-8 text-center text-sm text-muted-foreground">
            Aguardando dados ao vivo...
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Momentum & xG</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 33% 17%)" />
            <XAxis dataKey="minute" stroke="hsl(215 20% 65%)" fontSize={12} label={{ value: "Min", position: "insideBottom", offset: -5 }} />
            <YAxis stroke="hsl(215 20% 65%)" fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(222 47% 9%)",
                border: "1px solid hsl(217 33% 17%)",
                borderRadius: "6px",
              }}
            />
            <Legend />
            <Line type="monotone" dataKey="Mandante" stroke="hsl(142 76% 45%)" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="Visitante" stroke="hsl(217 91% 60%)" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="xG_M" stroke="hsl(142 76% 45%)" strokeWidth={1} strokeDasharray="5 5" dot={false} />
            <Line type="monotone" dataKey="xG_V" stroke="hsl(217 91% 60%)" strokeWidth={1} strokeDasharray="5 5" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
