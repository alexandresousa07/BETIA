"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatConfidence, getConfidenceLabel, getConfidenceVariant } from "@/lib/utils";
import type { Recommendation } from "@/lib/api";

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  return (
    <Card className="border-l-4 border-l-primary">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base">{recommendation.selection}</CardTitle>
            <p className="text-xs text-muted-foreground">
              Min {recommendation.minute} • Prob. {(recommendation.probability * 100).toFixed(1)}%
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-primary">
              {formatConfidence(recommendation.confidence_score)}
            </p>
            <Badge variant={getConfidenceVariant(recommendation.confidence_level)}>
              {getConfidenceLabel(recommendation.confidence_level)}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {recommendation.reasons && recommendation.reasons.length > 0 && (
          <div>
            <p className="mb-1 text-xs font-semibold uppercase text-muted-foreground">Motivos</p>
            <ul className="space-y-1">
              {recommendation.reasons.map((reason, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        )}

        {recommendation.explanation && (
          <div className="rounded-md bg-muted/50 p-3">
            <p className="mb-1 text-xs font-semibold uppercase text-muted-foreground">
              Explicação da IA
            </p>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {recommendation.explanation}
            </p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          {recommendation.positive_points && recommendation.positive_points.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-semibold text-success">Pontos Positivos</p>
              <ul className="space-y-0.5">
                {recommendation.positive_points.map((p, i) => (
                  <li key={i} className="text-xs text-muted-foreground">+ {p}</li>
                ))}
              </ul>
            </div>
          )}
          {recommendation.negative_points && recommendation.negative_points.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-semibold text-destructive">Riscos</p>
              <ul className="space-y-0.5">
                {recommendation.negative_points.map((p, i) => (
                  <li key={i} className="text-xs text-muted-foreground">- {p}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {recommendation.expected_value != null && (
          <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
            <span className="text-xs text-muted-foreground">Valor Esperado (EV)</span>
            <span className={`text-sm font-bold ${recommendation.expected_value > 0 ? "text-success" : "text-destructive"}`}>
              {recommendation.expected_value > 0 ? "+" : ""}{recommendation.expected_value.toFixed(1)}%
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
