"use client";

import { use } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Radio } from "lucide-react";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { MomentumChart } from "@/components/match/momentum-chart";
import { RecommendationCard } from "@/components/match/recommendation-card";
import { StatsPanel } from "@/components/match/stats-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const matchId = parseInt(id, 10);
  const queryClient = useQueryClient();

  const { data: match, isLoading } = useQuery({
    queryKey: ["match", matchId],
    queryFn: () => api.getMatchDetail(matchId),
    refetchInterval: (query) =>
      query.state.data?.is_monitored || query.state.data?.status === "live" ? 5_000 : 15_000,
    enabled: !isNaN(matchId),
  });

  const monitorMutation = useMutation({
    mutationFn: api.startMonitoring,
    onSuccess: (data) => {
      queryClient.setQueryData(["match", matchId], data);
    },
  });

  const refreshMutation = useMutation({
    mutationFn: api.refreshMatch,
    onSuccess: (data) => {
      queryClient.setQueryData(["match", matchId], data);
    },
  });

  const actionError = monitorMutation.error?.message || refreshMutation.error?.message;

  if (isLoading || !match) {
    return (
      <DashboardLayout>
        <div className="flex h-full items-center justify-center">
          <p className="text-muted-foreground">Carregando partida...</p>
        </div>
      </DashboardLayout>
    );
  }

  const latestStats = match.live_stats.length > 0
    ? match.live_stats[match.live_stats.length - 1]
    : null;

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6 flex items-center gap-4">
          <Link href="/matches">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              {match.status === "live" && (
                <Badge variant="destructive" className="gap-1">
                  <Radio className="h-3 w-3" />
                  AO VIVO {match.minute}&apos;
                </Badge>
              )}
              {match.is_monitored && <Badge variant="success">IA Monitorando</Badge>}
              {match.competition && (
                <span className="text-sm text-muted-foreground">{match.competition.name}</span>
              )}
            </div>
            <h1 className="mt-1 text-2xl font-bold">
              {match.home_team.name} {match.home_score} - {match.away_score} {match.away_team.name}
            </h1>
          </div>
          {!match.is_monitored && match.status === "live" && (
            <Button
              onClick={() => monitorMutation.mutate(matchId)}
              disabled={monitorMutation.isPending}
            >
              {monitorMutation.isPending ? "Iniciando..." : "Iniciar Monitoramento"}
            </Button>
          )}
          {match.is_monitored && (
            <Button
              variant="outline"
              onClick={() => refreshMutation.mutate(matchId)}
              disabled={refreshMutation.isPending}
            >
              {refreshMutation.isPending ? "Atualizando..." : "Atualizar Dados"}
            </Button>
          )}
        </div>

        {actionError && (
          <p className="mb-4 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-2 text-sm text-destructive">
            Erro ao atualizar: {actionError}. Verifique se o backend está online em localhost:8000.
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <MomentumChart stats={match.live_stats} />

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Entradas Sugeridas</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {match.recommendations.length === 0 ? (
                  <p className="py-4 text-center text-sm text-muted-foreground">
                    Nenhuma oportunidade detectada ainda
                  </p>
                ) : (
                  match.recommendations.map((rec) => (
                    <RecommendationCard key={rec.id} recommendation={rec} />
                  ))
                )}
              </CardContent>
            </Card>

            {match.events.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Timeline</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {match.events.map((event) => (
                      <div key={event.id} className="flex items-center gap-3 text-sm">
                        <span className="w-8 text-right font-mono text-muted-foreground">
                          {event.minute}&apos;
                        </span>
                        <span className="rounded bg-muted px-2 py-0.5 text-xs uppercase">
                          {event.event_type}
                        </span>
                        <span>{event.detail}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-6">
            <StatsPanel
              stats={latestStats}
              homeTeam={match.home_team.name}
              awayTeam={match.away_team.name}
            />

            {match.odds.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Odds</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {match.odds.slice(0, 8).map((odd, i) => (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{odd.selection}</span>
                        <span className="font-mono font-bold">{odd.odds_value.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
