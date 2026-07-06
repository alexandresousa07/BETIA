"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { MatchCard } from "@/components/match/match-card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function MatchesPage() {
  const queryClient = useQueryClient();

  const { data: matches = [], isLoading } = useQuery({
    queryKey: ["live-matches"],
    queryFn: api.getLiveMatches,
    refetchInterval: 30_000,
  });

  const syncMutation = useMutation({
    mutationFn: api.syncLiveMatches,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["live-matches"] }),
  });

  const monitorMutation = useMutation({
    mutationFn: api.startMonitoring,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["live-matches"] }),
  });

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Partidas</h1>
            <p className="text-sm text-muted-foreground">
              Selecione uma partida para monitoramento em tempo real
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${syncMutation.isPending ? "animate-spin" : ""}`} />
            Sincronizar
          </Button>
        </div>

        {isLoading ? (
          <p className="py-12 text-center text-muted-foreground">Carregando partidas...</p>
        ) : matches.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-muted-foreground">Nenhuma partida ao vivo encontrada.</p>
            <Button className="mt-4" onClick={() => syncMutation.mutate()}>
              Sincronizar com API-Football
            </Button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {matches.map((match) => (
              <MatchCard
                key={match.id}
                match={match}
                onMonitor={(id) => monitorMutation.mutate(id)}
              />
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
