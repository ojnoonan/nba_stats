import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { fetchGame, fetchGameStats } from "../services/api";
import { LoadingSpinner } from "../components/ui/loading-spinner";
import { SimpleTable } from "../components/simple/SimpleTable";

export default function GameDetailsPage() {
  const { id } = useParams();
  const [hideDNP, setHideDNP] = useState(false);

  const {
    data: game,
    isLoading: loadingGame,
    error: gameError,
  } = useQuery({
    queryKey: ["game", id],
    queryFn: () => fetchGame(id),
    enabled: !!id,
  });

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ["gameStats", id],
    queryFn: () => fetchGameStats(id),
    enabled: !!id && game?.status === "Final",
  });

  const formatDate = (dateStr) => {
    if (!dateStr) return "TBD";
    try {
      return format(new Date(dateStr), "MMMM d, yyyy 'at' h:mm a");
    } catch {
      return "TBD";
    }
  };

  const playerColumns = [
    {
      key: "player_name",
      header: "Player",
      render: (value, stat) => (
        <div>
          <div className="font-medium">{value}</div>
          <div className="text-sm text-muted-foreground">{stat.position}</div>
        </div>
      ),
    },
    {
      key: "minutes",
      header: "MIN",
      render: (value) => value || "0:00",
    },
    {
      key: "points",
      header: "PTS",
      render: (value) => value || 0,
    },
    {
      key: "rebounds",
      header: "REB",
      render: (value) => value || 0,
    },
    {
      key: "assists",
      header: "AST",
      render: (value) => value || 0,
    },
    {
      key: "steals",
      header: "STL",
      render: (value) => value || 0,
    },
    {
      key: "blocks",
      header: "BLK",
      render: (value) => value || 0,
    },
    {
      key: "field_goals_made",
      header: "FG",
      render: (value, stat) =>
        `${value || 0}/${stat.field_goals_attempted || 0}`,
    },
  ];

  if (loadingGame) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (gameError || !game) {
    return (
      <div className="flex items-center justify-center h-64" role="alert">
        <div className="text-center p-6 max-w-md">
          <div className="text-destructive text-xl mb-2">🏀</div>
          <h2 className="text-lg font-semibold text-destructive mb-2">
            Game not found
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
            {gameError?.message || "The requested game could not be found."}
          </p>
          <Link
            to="/games"
            className="inline-flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            ← Back to games
          </Link>
        </div>
      </div>
    );
  }

  // Filter stats by team and optionally hide DNP players
  const homeStats = stats?.filter((s) => s.team_id === game.home_team_id) || [];
  const awayStats = stats?.filter((s) => s.team_id === game.away_team_id) || [];

  const filteredHomeStats = hideDNP
    ? homeStats.filter((s) => s.minutes && s.minutes !== "0:00")
    : homeStats;

  const filteredAwayStats = hideDNP
    ? awayStats.filter((s) => s.minutes && s.minutes !== "0:00")
    : awayStats;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link
            to="/games"
            className="text-sm text-primary hover:underline mb-2 inline-block"
          >
            ← Back to games
          </Link>
          <h1 className="text-3xl font-bold">Game Details</h1>
          <p className="text-muted-foreground">{formatDate(game.game_date)}</p>
        </div>
      </div>

      {/* Game Summary */}
      <div className="bg-card p-6 rounded-lg border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-8">
            {/* Away Team */}
            <div className="text-center">
              <div className="text-lg font-semibold">{game.away_team_name}</div>
              <div className="text-3xl font-bold">
                {game.status === "Final" ? game.away_team_score || 0 : "-"}
              </div>
            </div>

            <div className="text-2xl text-muted-foreground">vs</div>

            {/* Home Team */}
            <div className="text-center">
              <div className="text-lg font-semibold">{game.home_team_name}</div>
              <div className="text-3xl font-bold">
                {game.status === "Final" ? game.home_team_score || 0 : "-"}
              </div>
            </div>
          </div>

          <div className="text-right">
            <div
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                game.status === "Final"
                  ? "bg-green-100 text-green-800"
                  : game.status === "In Progress"
                    ? "bg-blue-100 text-blue-800"
                    : "bg-gray-100 text-gray-800"
              }`}
            >
              {game.status}
            </div>
            {game.period && game.status !== "Final" && (
              <div className="text-sm text-muted-foreground mt-1">
                Period {game.period}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Player Stats */}
      {game.status === "Final" && stats && stats.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold">Player Statistics</h2>
            <label className="flex items-center space-x-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={hideDNP}
                onChange={(e) => setHideDNP(e.target.checked)}
                className="rounded focus:ring-2 focus:ring-primary focus:ring-offset-2"
                aria-describedby="hide-dnp-help"
              />
              <span>Hide inactive players</span>
              <span className="sr-only" id="hide-dnp-help">
                Toggle to show or hide players who did not play
              </span>
            </label>
          </div>

          {/* Away Team Stats */}
          <div>
            <h3 className="text-lg font-semibold mb-3">
              {game.away_team_name}
            </h3>
            <SimpleTable
              data={filteredAwayStats}
              columns={playerColumns}
              loading={loadingStats}
              emptyMessage="No player statistics available"
            />
          </div>

          {/* Home Team Stats */}
          <div>
            <h3 className="text-lg font-semibold mb-3">
              {game.home_team_name}
            </h3>
            <SimpleTable
              data={filteredHomeStats}
              columns={playerColumns}
              loading={loadingStats}
              emptyMessage="No player statistics available"
            />
          </div>
        </div>
      )}

      {/* No stats message for non-final games */}
      {game.status !== "Final" && (
        <div className="text-center py-12 text-muted-foreground">
          <p>Player statistics will be available when the game is completed.</p>
        </div>
      )}
    </div>
  );
}
