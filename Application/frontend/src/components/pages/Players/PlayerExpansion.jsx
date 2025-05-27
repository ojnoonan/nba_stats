import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { format } from "date-fns";
import { fetchPlayerStats, fetchTeams } from "../../../services/api";
import { LoadingSpinner } from "../../ui/loading-spinner";
import { PageLink } from "../../shared/Navigation";
import ExpandedContent from "../../shared/DataTable/ExpandedContent";

/**
 * Expandable content for player rows showing detailed stats and recent games
 */
const PlayerExpansion = ({
  player,
  showStats = true,
  showGameLog = true,
  showTeamInfo = true,
}) => {
  const {
    data: playerStats,
    isLoading: loadingStats,
    error: statsError,
  } = useQuery({
    queryKey: ["playerStats", player.player_id],
    queryFn: () => fetchPlayerStats(player.player_id),
    enabled: showGameLog,
  });

  const { data: teams } = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
    enabled: showTeamInfo && !!player.current_team_id,
  });

  const currentTeam = teams?.find((t) => t.team_id === player.current_team_id);

  const calculateAverages = (stats) => {
    if (!stats?.length) return null;

    const totals = stats.reduce(
      (acc, game) => {
        acc.points += game.points || 0;
        acc.rebounds += game.rebounds || 0;
        acc.assists += game.assists || 0;
        acc.games += 1;
        return acc;
      },
      { points: 0, rebounds: 0, assists: 0, games: 0 },
    );

    return {
      ppg: totals.games > 0 ? (totals.points / totals.games).toFixed(1) : "0.0",
      rpg:
        totals.games > 0 ? (totals.rebounds / totals.games).toFixed(1) : "0.0",
      apg:
        totals.games > 0 ? (totals.assists / totals.games).toFixed(1) : "0.0",
      games: totals.games,
    };
  };

  const averages = calculateAverages(playerStats);
  const recentGames = playerStats?.slice(0, 5) || [];

  return (
    <ExpandedContent loading={loadingStats} error={statsError}>
      <div className="space-y-6">
        {/* Player Info & Team */}
        {showTeamInfo && (
          <div className="flex items-center space-x-4 p-4 bg-muted/25 rounded-lg">
            <img
              src={player.headshot_url}
              alt={player.full_name}
              className="h-16 w-16 rounded-full object-cover"
              onError={(e) => {
                e.target.src = "/default-player.png";
              }}
            />
            <div className="flex-1">
              <h3 className="text-lg font-semibold">{player.full_name}</h3>
              <div className="text-sm text-muted-foreground space-y-1">
                <p>
                  {player.position}
                  {player.jersey_number && ` • #${player.jersey_number}`}
                  {player.height && ` • ${player.height}`}
                  {player.weight && ` • ${player.weight} lbs`}
                </p>
                {currentTeam && (
                  <div className="flex items-center space-x-2">
                    <img
                      src={currentTeam.logo_url}
                      alt={currentTeam.name}
                      className="h-4 w-4"
                    />
                    <Link
                      to={`/teams/${currentTeam.team_id}`}
                      className="hover:text-primary transition-colors"
                    >
                      {currentTeam.name}
                    </Link>
                  </div>
                )}
              </div>
            </div>
            <PageLink to={`/players/${player.player_id}`} variant="button">
              Full Profile
            </PageLink>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Season Averages */}
          {showStats && averages && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Season Averages</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-muted/25 rounded-lg">
                  <div className="text-2xl font-bold text-primary">
                    {averages.ppg}
                  </div>
                  <div className="text-sm text-muted-foreground">PPG</div>
                </div>
                <div className="text-center p-3 bg-muted/25 rounded-lg">
                  <div className="text-2xl font-bold text-primary">
                    {averages.rpg}
                  </div>
                  <div className="text-sm text-muted-foreground">RPG</div>
                </div>
                <div className="text-center p-3 bg-muted/25 rounded-lg">
                  <div className="text-2xl font-bold text-primary">
                    {averages.apg}
                  </div>
                  <div className="text-sm text-muted-foreground">APG</div>
                </div>
              </div>
              <div className="text-center mt-2 text-sm text-muted-foreground">
                {averages.games} games played
              </div>
            </div>
          )}

          {/* Recent Games */}
          {showGameLog && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Recent Games</h3>
                <PageLink
                  to={`/players/${player.player_id}`}
                  variant="text"
                  className="text-sm"
                >
                  Full Game Log
                </PageLink>
              </div>

              {loadingStats ? (
                <div className="flex items-center justify-center p-4">
                  <LoadingSpinner size="default" />
                </div>
              ) : statsError ? (
                <div className="text-destructive text-sm">
                  Failed to load game log
                </div>
              ) : recentGames.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {recentGames.map((game, index) => (
                    <div
                      key={game.game_id || index}
                      className="flex justify-between items-center p-3 rounded-md border"
                    >
                      <div className="text-sm">
                        <div className="font-medium">
                          {format(
                            new Date(game.game_date_utc || Date.now()),
                            "MMM d",
                          )}
                        </div>
                        <div className="text-muted-foreground">
                          {game.minutes || "0:00"} min
                        </div>
                      </div>
                      <div className="text-right text-sm">
                        <div className="font-semibold">
                          {game.points || 0} pts
                        </div>
                        <div className="text-muted-foreground">
                          {game.rebounds || 0}r • {game.assists || 0}a
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-muted-foreground text-sm p-4">
                  No recent games available
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </ExpandedContent>
  );
};

export default PlayerExpansion;
