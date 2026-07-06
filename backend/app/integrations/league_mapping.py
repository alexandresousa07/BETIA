"""Mapping between API-Football leagues and The Odds API sport keys."""

# API-Football league external_id -> The Odds API sport_key
LEAGUE_TO_ODDS_SPORT: dict[int, str] = {
    39: "soccer_epl",                      # Premier League
    140: "soccer_spain_la_liga",           # La Liga
    135: "soccer_italy_serie_a",           # Serie A
    78: "soccer_germany_bundesliga",       # Bundesliga
    61: "soccer_france_ligue_one",         # Ligue 1
    94: "soccer_portugal_primeira_liga",   # Primeira Liga
    71: "soccer_brazil_campeonato",        # Brasileirão
    128: "soccer_argentina_primera_division",
    2: "soccer_uefa_champs_league",        # Champions League
    3: "soccer_uefa_europa_league",        # Europa League
    848: "soccer_uefa_europa_conference_league",
    253: "soccer_usa_mls",
    88: "soccer_netherlands_eredivisie",
    144: "soccer_belgium_first_div",
    203: "soccer_turkey_super_league",
    262: "soccer_mexico_ligamx",
}

# Default leagues for historical training collection
DEFAULT_TRAINING_LEAGUES: list[int] = [39, 140, 135, 78, 61, 71, 94]

# The Odds API market key -> internal market key
ODDS_MARKET_MAP: dict[str, dict[str, str]] = {
    "totals": {
        "Over 2.5": "over_2.5_goals",
        "Under 2.5": "under_2.5_goals",
        "Over 1.5": "over_1.5_goals",
        "Over 9.5": "over_9.5_corners",
        "Under 9.5": "under_9.5_corners",
    },
    "h2h": {},  # mapped dynamically by team name
}

# Internal market -> selection pattern in odds for EV lookup
MARKET_TO_ODDS_SELECTION: dict[str, tuple[str, str]] = {
    "over_2.5_goals": ("totals", "Over 2.5"),
    "under_2.5_goals": ("totals", "Under 2.5"),
    "over_1.5_goals": ("totals", "Over 1.5"),
    "over_9.5_corners": ("totals", "Over 9.5"),
    "under_9.5_corners": ("totals", "Under 9.5"),
}
