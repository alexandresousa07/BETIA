"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent } from "@/components/ui/card";

export default function LogsPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="mb-2 text-2xl font-bold">Logs da IA</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          Registro de decisões, modelos utilizados e estatísticas consideradas
        </p>
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            Logs serão exibidos aqui conforme o monitoramento de partidas estiver ativo.
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
