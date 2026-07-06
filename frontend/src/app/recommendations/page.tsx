"use client";

import { useQuery } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { RecommendationCard } from "@/components/match/recommendation-card";
import { api } from "@/lib/api";

export default function RecommendationsPage() {
  const { data: recommendations = [], isLoading } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => api.getRecommendations(),
    refetchInterval: 15_000,
  });

  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="mb-2 text-2xl font-bold">Entradas da IA</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          Oportunidades detectadas pelo motor de consenso
        </p>

        {isLoading ? (
          <p className="text-center text-muted-foreground">Carregando...</p>
        ) : recommendations.length === 0 ? (
          <p className="py-12 text-center text-muted-foreground">Nenhuma entrada ativa</p>
        ) : (
          <div className="mx-auto max-w-3xl space-y-4">
            {recommendations.map((rec) => (
              <RecommendationCard key={rec.id} recommendation={rec} />
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
