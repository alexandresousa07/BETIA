"use client";

import { useQuery } from "@tanstack/react-query";
import { Brain, Radio, TrendingUp, Zap } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { MatchCard } from "@/components/match/match-card";
import { RecommendationCard } from "@/components/match/recommendation-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

function StatCard({
  title,
  value,
  icon: Icon,
  description,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  description?: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-4">
        <div className="rounded-lg bg-primary/10 p-3">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {description && <p className="text-xs text-muted-foreground">{description}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data: matches = [], isLoading: loadingMatches } = useQuery({
    queryKey: ["live-matches"],
    queryFn: api.getLiveMatches,
  });

  const { data: recommendations = [] } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => api.getRecommendations(),
  });

  const monitored = matches.filter((m) => m.is_monitored).length;
  const highConfidence = recommendations.filter((r) => r.confidence_score >= 70).length;

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Monitoramento inteligente de partidas em tempo real
          </p>
        </div>

        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Partidas ao Vivo" value={matches.length} icon={Radio} />
          <StatCard title="Monitorando" value={monitored} icon={Zap} />
          <StatCard title="Entradas Ativas" value={recommendations.length} icon={Brain} />
          <StatCard title="Alta Confiança" value={highConfidence} icon={TrendingUp} description="Score ≥ 70%" />
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Partidas ao Vivo</CardTitle>
              </CardHeader>
              <CardContent>
                {loadingMatches ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">Carregando...</p>
                ) : matches.length === 0 ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">
                    Nenhuma partida ao vivo. Configure sua API key e sincronize.
                  </p>
                ) : (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {matches.slice(0, 6).map((match) => (
                      <MatchCard key={match.id} match={match} />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Últimas Entradas</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {recommendations.length === 0 ? (
                  <p className="py-4 text-center text-sm text-muted-foreground">
                    Nenhuma entrada detectada
                  </p>
                ) : (
                  recommendations.slice(0, 3).map((rec) => (
                    <RecommendationCard key={rec.id} recommendation={rec} />
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
