"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="mb-2 text-2xl font-bold">Configurações</h1>
        <p className="mb-6 text-sm text-muted-foreground">Preferências do usuário e alertas</p>

        <div className="mx-auto max-w-2xl space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Alertas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <label className="flex items-center justify-between">
                <span className="text-sm">Som de alerta</span>
                <input type="checkbox" defaultChecked className="h-4 w-4 accent-primary" />
              </label>
              <label className="flex items-center justify-between">
                <span className="text-sm">Notificações push</span>
                <input type="checkbox" defaultChecked className="h-4 w-4 accent-primary" />
              </label>
              <label className="flex items-center justify-between">
                <span className="text-sm">Confiança mínima</span>
                <input type="range" min="50" max="95" defaultValue="70" className="w-32 accent-primary" />
              </label>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">API Keys</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Configure API_FOOTBALL_KEY e THE_ODDS_API_KEY no arquivo .env do backend.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
