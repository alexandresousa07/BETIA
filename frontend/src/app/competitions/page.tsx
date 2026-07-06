"use client";

import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Globe, RefreshCw, Search } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { CompetitionCard } from "@/components/competition/competition-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, type Competition } from "@/lib/api";

export default function CompetitionsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [countryCode, setCountryCode] = useState<string>("");
  const [leagueType, setLeagueType] = useState<string>("");

  const { data: countries = [] } = useQuery({
    queryKey: ["competition-countries"],
    queryFn: api.getCompetitionCountries,
  });

  const { data: competitions = [], isLoading } = useQuery({
    queryKey: ["competitions", countryCode, leagueType, search],
    queryFn: () =>
      api.getCompetitions({
        country_code: countryCode || undefined,
        league_type: leagueType || undefined,
        search: search || undefined,
        status: "active",
      }),
  });

  const syncMutation = useMutation({
    mutationFn: () => api.syncCompetitions(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["competitions"] });
      queryClient.invalidateQueries({ queryKey: ["competition-countries"] });
    },
  });

  const grouped = useMemo(() => {
    const map = new Map<string, Competition[]>();
    for (const comp of competitions) {
      const key = comp.country || "Internacional";
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(comp);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [competitions]);

  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-2xl font-bold">Competições</h1>
            <p className="text-sm text-muted-foreground">
              Selecione qualquer liga sincronizada automaticamente da API-Football
            </p>
          </div>
          <Button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${syncMutation.isPending ? "animate-spin" : ""}`} />
            Sincronizar Ligas
          </Button>
        </div>

        <Card className="mb-6">
          <CardContent className="flex flex-col gap-3 p-4 lg:flex-row lg:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                className="w-full rounded-md border border-border bg-background py-2 pl-10 pr-3 text-sm"
                placeholder="Buscar liga ou país..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <select
              className="rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={countryCode}
              onChange={(e) => setCountryCode(e.target.value)}
            >
              <option value="">Todos os países</option>
              {countries.map((c) => (
                <option key={c.country_code} value={c.country_code}>
                  {c.flag_emoji} {c.country} ({c.count})
                </option>
              ))}
            </select>
            <select
              className="rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={leagueType}
              onChange={(e) => setLeagueType(e.target.value)}
            >
              <option value="">Todos os tipos</option>
              <option value="League">Liga</option>
              <option value="Cup">Copa</option>
            </select>
          </CardContent>
        </Card>

        {isLoading ? (
          <p className="py-12 text-center text-muted-foreground">Carregando competições...</p>
        ) : competitions.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Globe className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
              <p className="text-muted-foreground">
                Nenhuma competição no banco. Clique em &quot;Sincronizar Ligas&quot; para importar da API.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-8">
            {grouped.map(([country, items]) => (
              <div key={country}>
                <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  {items[0]?.flag_emoji} {country}
                </h2>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {items.map((comp) => (
                    <CompetitionCard key={comp.id} competition={comp} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
