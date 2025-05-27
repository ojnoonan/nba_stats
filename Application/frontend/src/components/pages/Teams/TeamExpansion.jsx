import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { format } from "date-fns";
import { formatInTimeZone } from "date-fns-tz";
import { fetchPlayers, fetchGames } from "../../../services/api";
import { LoadingSpinner } from "../../ui/loading-spinner";
import { PageLink } from "../../shared/Navigation";
import ExpandedContent from "../../shared/DataTable/ExpandedContent";

/**
 * Expandable content for team rows showing roster and recent games
 */
const TeamExpansion = ({
  team,
  showStats = true,
  showRoster = true,
  showRecentGames = true,
}) => {
  const {
    data: teamPlayers,
    isLoading: loadingPlayers,
    error: playersError,
  } = useQuery({
    queryKey: ["players", team.team_id],
    queryFn: () => fetchPlayers(team.team_id),
    enabled: showRoster,
  });

  const {
    data: teamGames,
    isLoading: loadingGames,
    error: gamesError,
  } = useQuery({
    queryKey: ["games", team.team_id],
    queryFn: () => fetchGames(team.team_id),
    enabled: showRecentGames,
  });

  const formatGameTime = (dateStr) => {
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return formatInTimeZone(new Date(dateStr), timeZone, "h:mm a 'GMT'XXX");
  };

  const sortGamesByDate = (games) => {
    if (!games) return [];
    return [...games].sort(
      (a, b) => new Date(b.game_date_utc) - new Date(a.game_date_utc),
    );
  };

  const isLoading = loadingPlayers || loadingGames;
  const error = playersError || gamesError;

  return (
    <ExpandedContent loading={isLoading} error={error}>
      <div className="space-y-6">
        {/* Team Stats Section */}
        {showStats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-muted/25 rounded-lg">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {team.wins || 0}
              </div>
              <div className="text-sm text-muted-foreground">Wins</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-destructive">
                {team.losses || 0}
              </div>
              <div className="text-sm text-muted-foreground">Losses</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium">
                {team.conference || "N/A"}
              </div>
              <div className="text-sm text-muted-foreground">Conference</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-medium">
                {team.division || "N/A"}
              </div>
              <div className="text-sm text-muted-foreground">Division</div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Current Roster Section */}
          {showRoster && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Current Roster</h3>
                <PageLink
                  to={`/teams/${team.team_id}`}
                  variant="text"
                  className="text-sm"
                >
                  View Full Team
                </PageLink>
              </div>

              {loadingPlayers ? (
                <div className="flex items-center justify-center p-4">
                  <LoadingSpinner size="default" />
                </div>
              ) : playersError ? (
                <div className="text-destructive text-sm">
                  Failed to load roster
                </div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {teamPlayers?.slice(0, 8).map((player) => (
                    <Link
                      key={player.player_id}
                      to={`/players/${player.player_id}`}
                      className="flex items-center space-x-3 p-2 rounded-md hover:bg-muted/50 transition-colors"
                    >
                      <img
                        src={player.headshot_url}
                        alt={player.full_name}
                        className="h-8 w-8 rounded-full object-cover"
                        onError={(e) => {
                          e.target.src = "/default-player.png";
                        }}
                      />
                      <div className="flex-1">
                        <p className="font-medium text-sm">
                          {player.full_name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {player.position}
                          {player.jersey_number && ` #${player.jersey_number}`}
                        </p>
                      </div>
                    </Link>
                  ))}
                  {teamPlayers?.length > 8 && (
                    <div className="text-center pt-2">
                      <PageLink
                        to={`/teams/${team.team_id}`}
                        variant="text"
                        className="text-sm"
                      >
                        +{teamPlayers.length - 8} more players
                      </PageLink>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Recent Games Section */}
          {showRecentGames && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Recent Games</h3>
                <PageLink
                  to={`/teams/${team.team_id}`}
                  variant="text"
                  className="text-sm"
                >
                  View Schedule
                </PageLink>
              </div>

              {loadingGames ? (
                <div className="flex items-center justify-center p-4">
                  <LoadingSpinner size="default" />
                </div>
              ) : gamesError ? (
                <div className="text-destructive text-sm">
                  Failed to load games
                </div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {sortGamesByDate(teamGames)
                    ?.slice(0, 5)
                    .map((game) => (
                      <Link
                        key={game.game_id}
                        to={`/games/${game.game_id}`}
                        className="block p-3 rounded-md border hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex justify-between items-center">
                          <div className="text-sm">
                            <div className="font-medium">
                              {game.home_team_id === team.team_id ? "vs" : "@"}
                              {/* This would need team lookup, simplified for now */}
                            </div>
                            <div className="text-muted-foreground">
                              {format(
                                new Date(game.game_date_utc),
                                "MMM d, yyyy",
                              )}
                            </div>
                          </div>
                          {game.status === "Completed" && (
                            <div className="text-right text-sm">
                              <div className="font-semibold">
                                {game.home_team_id === team.team_id
                                  ? `${game.home_score} - ${game.away_score}`
                                  : `${game.away_score} - ${game.home_score}`}
                              </div>
                              <div
                                className={`text-xs ${
                                  (game.home_team_id === team.team_id &&
                                    game.home_score > game.away_score) ||
                                  (game.away_team_id === team.team_id &&
                                    game.away_score > game.home_score)
                                    ? "text-green-500"
                                    : "text-red-500"
                                }`}
                              >
                                {(game.home_team_id === team.team_id &&
                                  game.home_score > game.away_score) ||
                                (game.away_team_id === team.team_id &&
                                  game.away_score > game.home_score)
                                  ? "W"
                                  : "L"}
                              </div>
                            </div>
                          )}
                          {game.status === "Upcoming" && (
                            <div className="text-sm text-muted-foreground">
                              {formatGameTime(game.game_date_utc)}
                            </div>
                          )}
                        </div>
                      </Link>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </ExpandedContent>
  );
};

export default TeamExpansion;
