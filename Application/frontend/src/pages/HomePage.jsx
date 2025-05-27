import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { format } from "date-fns";
import {
  fetchTeams,
  fetchPlayers,
  fetchGames,
  fetchStatus,
} from "../services/api";
import { LoadingSpinner } from "../components/ui/loading-spinner";

const HomePage = () => {
  const { data: teams } = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const { data: players } = useQuery({
    queryKey: ["players"],
    queryFn: () => fetchPlayers(null, true),
  });

  const { data: games } = useQuery({
    queryKey: ["games"],
    queryFn: () => fetchGames(),
  });

  const { data: status } = useQuery({
    queryKey: ["status"],
    queryFn: fetchStatus,
    refetchInterval: 30000, // Reduced frequency
  });

  // Get recent games for highlights
  const recentGames =
    games
      ?.filter((game) => game.status === "Final")
      .sort((a, b) => new Date(b.date) - new Date(a.date))
      .slice(0, 3) || [];

  const upcomingGames =
    games
      ?.filter((game) => game.status === "Upcoming")
      .sort((a, b) => new Date(a.date) - new Date(b.date))
      .slice(0, 3) || [];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold mb-4">NBA Stats</h1>
        <p className="text-xl text-muted-foreground mb-8">
          Explore teams, players, and games with a clean, simple interface
        </p>

        {status?.is_updating && (
          <div
            className="flex items-center justify-center space-x-2 text-primary"
            role="status"
            aria-live="polite"
          >
            <LoadingSpinner size="small" />
            <span>Updating {status.current_phase || "data"}...</span>
            <span className="sr-only">Data is being updated, please wait</span>
          </div>
        )}
      </div>

      {/* Navigation Cards */}
      <div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        role="navigation"
        aria-label="Main navigation"
      >
        <Link
          to="/teams"
          className="group bg-card p-6 rounded-lg border hover:border-primary transition-colors"
        >
          <div className="text-center">
            <div className="text-3xl font-bold text-primary mb-2">
              {teams?.length || 0}
            </div>
            <h3 className="text-lg font-semibold mb-2">Teams</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Browse all NBA teams and their rosters
            </p>
            <div className="text-primary group-hover:underline">
              View Teams →
            </div>
          </div>
        </Link>

        <Link
          to="/players"
          className="group bg-card p-6 rounded-lg border hover:border-primary transition-colors"
        >
          <div className="text-center">
            <div className="text-3xl font-bold text-primary mb-2">
              {players?.length || 0}
            </div>
            <h3 className="text-lg font-semibold mb-2">Players</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Explore player stats and performance
            </p>
            <div className="text-primary group-hover:underline">
              View Players →
            </div>
          </div>
        </Link>

        <Link
          to="/games"
          className="group bg-card p-6 rounded-lg border hover:border-primary transition-colors"
        >
          <div className="text-center">
            <div className="text-3xl font-bold text-primary mb-2">
              {games?.filter((g) => g.status === "Final").length || 0}
            </div>
            <h3 className="text-lg font-semibold mb-2">Games</h3>
            <p className="text-sm text-muted-foreground mb-4">
              View completed game results and stats
            </p>
            <div className="text-primary group-hover:underline">
              View Games →
            </div>
          </div>
        </Link>

        <Link
          to="/upcoming-games"
          className="group bg-card p-6 rounded-lg border hover:border-primary transition-colors"
        >
          <div className="text-center">
            <div className="text-3xl font-bold text-primary mb-2">
              {upcomingGames?.length || 0}
            </div>
            <h3 className="text-lg font-semibold mb-2">Upcoming</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Check upcoming game schedules
            </p>
            <div className="text-primary group-hover:underline">
              View Schedule →
            </div>
          </div>
        </Link>
      </div>

      {/* Recent Games Highlights */}
      {recentGames.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">Recent Games</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recentGames.map((game) => (
              <Link
                key={game.id}
                to={`/games/${game.id}`}
                className="bg-card p-4 rounded-lg border hover:border-primary transition-colors"
              >
                <div className="text-sm text-muted-foreground mb-2">
                  {format(new Date(game.date), "MMM d, yyyy")}
                </div>
                <div className="flex justify-between items-center">
                  <div className="text-center">
                    <div className="font-medium">{game.away_team_name}</div>
                    <div className="text-2xl font-bold">
                      {game.away_team_score}
                    </div>
                  </div>
                  <div className="text-muted-foreground">vs</div>
                  <div className="text-center">
                    <div className="font-medium">{game.home_team_name}</div>
                    <div className="text-2xl font-bold">
                      {game.home_team_score}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Upcoming Games Preview */}
      {upcomingGames.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">Upcoming Games</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {upcomingGames.map((game) => (
              <div key={game.id} className="bg-card p-4 rounded-lg border">
                <div className="text-sm text-muted-foreground mb-2">
                  {format(new Date(game.date), "MMM d, yyyy 'at' h:mm a")}
                </div>
                <div className="flex justify-between items-center">
                  <div className="text-center">
                    <div className="font-medium">{game.away_team_name}</div>
                  </div>
                  <div className="text-muted-foreground">@</div>
                  <div className="text-center">
                    <div className="font-medium">{game.home_team_name}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Simple status footer */}
      {status?.last_update && (
        <div className="text-center text-sm text-muted-foreground border-t pt-6">
          Data last updated:{" "}
          {format(new Date(status.last_update), "MMM d, yyyy 'at' h:mm a")}
        </div>
      )}
    </div>
  );
};

export default HomePage;
