import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatConfidence(score: number): string {
  return `${score.toFixed(0)}%`;
}

export function getConfidenceVariant(level: string): "success" | "warning" | "destructive" | "default" {
  switch (level) {
    case "very_high":
    case "high":
      return "success";
    case "medium":
      return "warning";
    case "low":
      return "destructive";
    default:
      return "default";
  }
}

export function getConfidenceLabel(level: string): string {
  const labels: Record<string, string> = {
    very_high: "Muito Alta",
    high: "Alta",
    medium: "Média",
    low: "Baixa",
  };
  return labels[level] || level;
}
