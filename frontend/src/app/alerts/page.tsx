"use client";

import { useQuery } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatConfidence, getConfidenceLabel, getConfidenceVariant } from "@/lib/utils";
import { api } from "@/lib/api";

export default function AlertsPage() {
  const { data: recommendations = [] } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => api.getRecommendations(),
    refetchInterval: 10_000,
  });

  const alerts = recommendations.filter((r) => r.confidence_score >= 70);

  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="mb-2 text-2xl font-bold">Alertas</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          Oportunidades de alta confiança em tempo real
        </p>

        {alerts.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Bell className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
              <p className="text-muted-foreground">Nenhum alerta ativo no momento</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <Card key={alert.id} className="border-l-4 border-l-warning">
                <CardContent className="flex items-center justify-between p-4">
                  <div>
                    <p className="font-semibold">{alert.selection}</p>
                    <p className="text-sm text-muted-foreground">
                      Min {alert.minute} • Prob. {(alert.probability * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-primary">
                      {formatConfidence(alert.confidence_score)}
                    </p>
                    <Badge variant={getConfidenceVariant(alert.confidence_level)}>
                      {getConfidenceLabel(alert.confidence_level)}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
