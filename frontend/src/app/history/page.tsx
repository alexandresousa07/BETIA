"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent } from "@/components/ui/card";

export default function HistoryPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="mb-2 text-2xl font-bold">Histórico</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          Registro de entradas anteriores e resultados
        </p>
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            O histórico será populado conforme as partidas forem finalizadas e os resultados calculados.
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
