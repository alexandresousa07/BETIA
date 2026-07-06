const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface APIResponse<T> {
  success: boolean;
  data: T;
  message: string;
  timestamp: string;
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  const json: APIResponse<T> = await response.json();
  return json.data;
}

export const api = {
  getLiveMatches: () => fetchAPI<Match[]>("/api/v1/matches/live"),
  getMatchDetail: (id: number) => fetchAPI<MatchDetail>(`/api/v1/matches/${id}`),
  startMonitoring: (matchId: number) =>
    fetchAPI<MatchDetail>("/api/v1/matches/monitor", {
      method: "POST",
      body: JSON.stringify({ match_id: matchId }),
    }),
  refreshMatch: (matchId: number) =>
    fetchAPI<MatchDetail>(`/api/v1/matches/${matchId}/refresh`, { method: "POST" }),
  getRecommendations: (matchId?: number) =>
    fetchAPI<Recommendation[]>(
      `/api/v1/recommendations${matchId ? `?match_id=${matchId}` : ""}`
    ),
  syncLiveMatches: () =>
    fetchAPI<{ count: number }>("/api/v1/matches/sync", { method: "POST" }),
  getHealth: () => fetchAPI<{ status: string; app: string }>("/api/v1/health"),
  getCompetitions: (params?: {
    country_code?: string;
    status?: string;
    league_type?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.country_code) query.set("country_code", params.country_code);
    if (params?.status) query.set("status", params.status);
    if (params?.league_type) query.set("league_type", params.league_type);
    if (params?.search) query.set("search", params.search);
    const qs = query.toString();
    return fetchAPI<Competition[]>(`/api/v1/competitions${qs ? `?${qs}` : ""}`);
  },
  getCompetitionCountries: () =>
    fetchAPI<CompetitionCountry[]>("/api/v1/competitions/countries"),
  syncCompetitions: (season?: number) =>
    fetchAPI<CompetitionSyncResult>(
      `/api/v1/competitions/sync${season ? `?season=${season}` : ""}`,
      { method: "POST" }
    ),
  syncCompetitionMatches: (competitionId: number, date?: string) =>
    fetchAPI<{ fixtures_synced: number; match_ids: number[] }>(
      `/api/v1/competitions/${competitionId}/sync-matches${date ? `?date=${date}` : ""}`,
      { method: "POST" }
    ),
  getCompetition: (id: number) => fetchAPI<Competition>(`/api/v1/competitions/${id}`),
};

export interface Competition {
  id: number;
  external_id: number;
  name: string;
  country?: string;
  country_code?: string;
  country_flag_url?: string;
  flag_emoji?: string;
  logo_url?: string;
  season?: string;
  season_year?: number;
  league_type?: string;
  status: string;
  odds_sport_key?: string;
  synced_at?: string;
}

export interface CompetitionCountry {
  country_code: string;
  country: string;
  count: number;
  flag_emoji: string;
}

export interface CompetitionSyncResult {
  season: number;
  fetched: number;
  created: number;
  updated: number;
  total_in_db: number;
  active_in_db: number;
}

export interface Team {
  id: number;
  external_id: number;
  name: string;
  logo_url?: string;
}

export interface Match {
  id: number;
  external_id: number;
  status: string;
  kickoff_at?: string;
  minute?: number;
  home_score: number;
  away_score: number;
  is_monitored: boolean;
  home_team: Team;
  away_team: Team;
  competition?: { id: number; name: string; country?: string; logo_url?: string };
}

export interface LiveStat {
  minute: number;
  possession_home?: number;
  possession_away?: number;
  shots_home: number;
  shots_away: number;
  shots_on_target_home: number;
  shots_on_target_away: number;
  xg_home: number;
  xg_away: number;
  momentum_home: number;
  momentum_away: number;
  offensive_pressure_home: number;
  offensive_pressure_away: number;
  corners_home: number;
  corners_away: number;
  recorded_at: string;
}

export interface Recommendation {
  id: number;
  market: string;
  selection: string;
  confidence_score: number;
  confidence_level: string;
  probability: number;
  expected_value?: number;
  odds_at_creation?: number;
  reasons?: string[];
  positive_points?: string[];
  negative_points?: string[];
  model_contributions?: Record<string, number>;
  explanation?: string;
  minute: number;
  is_active: boolean;
  created_at: string;
}

export interface MatchDetail extends Match {
  live_stats: LiveStat[];
  events: { id: number; minute: number; event_type: string; detail?: string }[];
  odds: { market: string; selection: string; bookmaker: string; odds_value: number }[];
  predictions: { market: string; probability: number; model_name: string; minute: number }[];
  recommendations: Recommendation[];
}
