import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { format } from "date-fns";
import { fetchGameStats, fetchTeams } from "../../../services/api";
import { LoadingSpinner } from "../../ui/loading-spinner";
import { PageLink } from "../../shared/Navigation";
import ExpandedContent from "../../shared/DataTable/ExpandedContent";

/**
 * Expandable content for game rows showing box scores and key plays
 */
const GameExpansion = ({
  game,
  showBoxScore = true,
  showTeamComparison = true,
}) => {
  const {
    data: gameStats,
    isLoading: loadingStats,
    error: statsError,
  } = useQuery({
    queryKey: ["gameStats", game.game_id],
    queryFn: () => fetchGameStats(game.game_id),
    enabled: showBoxScore && game.status === "Completed",
  });

  const { data: teams } = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const homeTeam = teams?.find((t) => t.team_id === game.home_team_id);
  const awayTeam = teams?.find((t) => t.team_id === game.away_team_id);

  const getTopPerformers = (stats) => {
    if (!stats?.length) return { home: [], away: [] };

    const homeStats = stats.filter((s) => s.team_id === game.home_team_id);
    const awayStats = stats.filter((s) => s.team_id === game.away_team_id);

    const sortByPoints = (a, b) => (b.points || 0) - (a.points || 0);

    return {
      home: homeStats.sort(sortByPoints).slice(0, 3),
      away: awayStats.sort(sortByPoints).slice(0, 3),
    };
  };

  const topPerformers = getTopPerformers(gameStats);

  const formatDate = (dateStr) => {
    return format(new Date(dateStr), "MMM d, yyyy h:mm a");
  };

  return (
    <ExpandedContent loading={loadingStats} error={statsError}>
      <div className="space-y-6">
        {/* Game Header Info */}
        <div className="text-center p-4 bg-muted/25 rounded-lg">
          <div className="text-sm text-muted-foreground mb-2">
            {formatDate(game.game_date_utc)}
          </div>
          {game.playoff_round && (
            <div className="text-lg font-semibold text-primary mb-4">
              {game.playoff_round}
            </div>
          )}
          <div className="grid grid-cols-3 items-center gap-4">
            <div className="text-center">
              {awayTeam && (
                <>
                  <img
                    src={awayTeam.logo_url}
                    alt={awayTeam.name}
                    className="mx-auto h-12 w-12 object-contain mb-2"
                  />
                  <div className="font-semibold">{awayTeam.name}</div>
                </>
              )}
              {game.status === "Completed" && (
                <div className="text-2xl font-bold mt-2">{game.away_score}</div>
              )}
            </div>
            <div className="text-center">
              <div className="text-lg font-medium">
                {game.status === "Completed" ? "Final" : game.status}
              </div>
              <PageLink
                to={`/games/${game.game_id}`}
                variant="button"
                className="mt-2"
              >
                Full Details
              </PageLink>
            </div>
            <div className="text-center">
              {homeTeam && (
                <>
                  <img
                    src={homeTeam.logo_url}
                    alt={homeTeam.name}
                    className="mx-auto h-12 w-12 object-contain mb-2"
                  />
                  <div className="font-semibold">{homeTeam.name}</div>
                </>
              )}
              {game.status === "Completed" && (
                <div className="text-2xl font-bold mt-2">{game.home_score}</div>
              )}
            </div>
          </div>
        </div>

        {/* Top Performers - Only show for completed games */}
        {showBoxScore && game.status === "Completed" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Away Team Top Performers */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                {awayTeam && (
                  <img
                    src={awayTeam.logo_url}
                    alt={awayTeam.name}
                    className="h-5 w-5 mr-2"
                  />
                )}
                {awayTeam?.name} Leaders
              </h3>

              {loadingStats ? (
                <div className="flex items-center justify-center p-4">
                  <LoadingSpinner size="default" />
                </div>
              ) : topPerformers.away.length > 0 ? (
                <div className="space-y-2">
                  {topPerformers.away.map((stat, index) => (
                    <div
                      key={stat.stat_id || index}
                      className="flex justify-between items-center p-3 rounded-md border"
                    >
                      <div className="flex items-center space-x-2">
                        <div className="text-sm font-medium">{index + 1}.</div>
                        <div>
                          <div className="font-medium text-sm">
                            {stat.player_name}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {stat.minutes} min
                          </div>
                        </div>
                      </div>
                      <div className="text-right text-sm">
                        <div className="font-semibold">{stat.points} pts</div>
                        <div className="text-muted-foreground">
                          {stat.rebounds}r • {stat.assists}a
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-muted-foreground text-sm p-4">
                  No stats available
                </div>
              )}
            </div>

            {/* Home Team Top Performers */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                {homeTeam && (
                  <img
                    src={homeTeam.logo_url}
                    alt={homeTeam.name}
                    className="h-5 w-5 mr-2"
                  />
                )}
                {homeTeam?.name} Leaders
              </h3>

              {loadingStats ? (
                <div className="flex items-center justify-center p-4">
                  <LoadingSpinner size="default" />
                </div>
              ) : topPerformers.home.length > 0 ? (
                <div className="space-y-2">
                  {topPerformers.home.map((stat, index) => (
                    <div
                      key={stat.stat_id || index}
                      className="flex justify-between items-center p-3 rounded-md border"
                    >
                      <div className="flex items-center space-x-2">
                        <div className="text-sm font-medium">{index + 1}.</div>
                        <div>
                          <div className="font-medium text-sm">
                            {stat.player_name}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {stat.minutes} min
                          </div>
                        </div>
                      </div>
                      <div className="text-right text-sm">
                        <div className="font-semibold">{stat.points} pts</div>
                        <div className="text-muted-foreground">
                          {stat.rebounds}r • {stat.assists}a
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-muted-foreground text-sm p-4">
                  No stats available
                </div>
              )}
            </div>
          </div>
        )}

        {/* Upcoming Game Info */}
        {game.status === "Upcoming" && (
          <div className="text-center p-4 bg-muted/25 rounded-lg">
            <p className="text-muted-foreground">
              This game hasn't started yet. Check back after{" "}
              {formatDate(game.game_date_utc)} for the box score.
            </p>
          </div>
        )}
      </div>
    </ExpandedContent>
  );
};

export default GameExpansion;
