"use client";

import Link from "next/link";
import { Eye, Radio } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Match } from "@/lib/api";

interface MatchCardProps {
  match: Match;
  onMonitor?: (matchId: number) => void;
}

export function MatchCard({ match, onMonitor }: MatchCardProps) {
  const isLive = match.status === "live";

  return (
    <Card className="transition-colors hover:border-primary/30">
      <CardContent className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isLive && (
              <Badge variant="destructive" className="gap-1">
                <Radio className="h-3 w-3" />
                AO VIVO {match.minute}&apos;
              </Badge>
            )}
            {match.is_monitored && <Badge variant="success">Monitorando</Badge>}
          </div>
          {match.competition && (
            <span className="text-xs text-muted-foreground">{match.competition.name}</span>
          )}
        </div>

        <div className="flex items-center justify-between">
          <div className="flex flex-1 flex-col items-center gap-1">
            <span className="text-sm font-medium">{match.home_team.name}</span>
          </div>

          <div className="mx-4 flex flex-col items-center">
            <span className="text-2xl font-bold tabular-nums">
              {match.home_score} - {match.away_score}
            </span>
          </div>

          <div className="flex flex-1 flex-col items-center gap-1">
            <span className="text-sm font-medium">{match.away_team.name}</span>
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <Link href={`/matches/${match.id}`} className="flex-1">
            <Button variant="outline" className="w-full" size="sm">
              <Eye className="mr-2 h-3 w-3" />
              Analisar
            </Button>
          </Link>
          {onMonitor && !match.is_monitored && isLive && (
            <Button variant="default" size="sm" onClick={() => onMonitor(match.id)}>
              Monitorar
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
