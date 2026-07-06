"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { Competition } from "@/lib/api";
import Link from "next/link";

interface CompetitionCardProps {
  competition: Competition;
  onSelect?: (competition: Competition) => void;
  selected?: boolean;
}

export function CompetitionCard({ competition, onSelect, selected }: CompetitionCardProps) {
  return (
    <Card
      className={`transition-colors hover:border-primary/40 ${
        selected ? "border-primary bg-primary/5" : ""
      }`}
    >
      <CardContent className="p-4">
        <div
          className="flex cursor-pointer items-center gap-3"
          onClick={() => onSelect?.(competition)}
        >
          <span className="text-2xl">{competition.flag_emoji || "🌎"}</span>
          {competition.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={competition.logo_url} alt="" className="h-8 w-8 object-contain" />
          ) : null}
          <div className="min-w-0 flex-1">
            <p className="truncate font-medium">{competition.name}</p>
            <p className="text-xs text-muted-foreground">
              {competition.country}
              {competition.season ? ` • ${competition.season}` : ""}
              {competition.league_type ? ` • ${competition.league_type}` : ""}
            </p>
          </div>
          <div className="text-right">
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                competition.status === "active"
                  ? "bg-success/20 text-success"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {competition.status}
            </span>
            <p className="mt-1 text-[10px] text-muted-foreground">ID {competition.external_id}</p>
          </div>
        </div>
        <Link href={`/competitions/${competition.id}`} className="mt-3 block">
          <Button variant="outline" size="sm" className="w-full">
            Ver partidas
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}

export function CompetitionCardLink({ competition }: { competition: Competition }) {
  return (
    <Link href={`/competitions/${competition.id}`}>
      <CompetitionCard competition={competition} />
    </Link>
  );
}
