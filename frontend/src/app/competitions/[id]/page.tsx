"use client";

import { use } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { MatchCard } from "@/components/match/match-card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function CompetitionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const competitionId = parseInt(id, 10);
  const queryClient = useQueryClient();

  const { data: competition, isLoading } = useQuery({
    queryKey: ["competition", competitionId],
    queryFn: () => api.getCompetition(competitionId),
    enabled: !isNaN(competitionId),
  });

  const { data: matches = [], refetch } = useQuery({
    queryKey: ["live-matches"],
    queryFn: api.getLiveMatches,
  });

  const filteredMatches = matches.filter(
    (m) => m.competition?.id === competitionId
  );

  const syncMutation = useMutation({
    mutationFn: () => api.syncCompetitionMatches(competitionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["live-matches"] });
      refetch();
    },
  });

  const monitorMutation = useMutation({
    mutationFn: api.startMonitoring,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["live-matches"] }),
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex h-full items-center justify-center">
          <p className="text-muted-foreground">Carregando...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (!competition) {
    return (
      <DashboardLayout>
        <div className="flex h-full items-center justify-center">
          <p className="text-muted-foreground">Competição não encontrada. Sincronize as ligas primeiro.</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6 flex items-center gap-4">
          <Link href="/competitions">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{competition.flag_emoji}</span>
              <h1 className="text-2xl font-bold">{competition.name}</h1>
            </div>
            <p className="text-sm text-muted-foreground">
              {competition.country} • Temporada {competition.season} • ID {competition.external_id}
            </p>
          </div>
          <Button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${syncMutation.isPending ? "animate-spin" : ""}`} />
            Sincronizar Partidas
          </Button>
        </div>

        {filteredMatches.length === 0 ? (
          <p className="py-12 text-center text-muted-foreground">
            Nenhuma partida ao vivo desta competição. Clique em Sincronizar Partidas.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredMatches.map((match) => (
              <MatchCard
                key={match.id}
                match={match}
                onMonitor={(mid) => monitorMutation.mutate(mid)}
              />
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
