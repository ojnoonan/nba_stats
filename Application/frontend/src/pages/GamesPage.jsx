import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { format } from "date-fns";
import { fetchGames, fetchTeams } from "../services/api";
import { LoadingSpinner } from "../components/ui/loading-spinner";
import { SimpleTable } from "../components/simple/SimpleTable";
import { optimizedNavigate } from "../utils/performance";

const GamesPage = () => {
  const {
    data: games,
    isLoading: gamesLoading,
    error: gamesError,
  } = useQuery({
    queryKey: ["games"],
    queryFn: () => fetchGames(),
  });

  const { data: teams } = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const formatGameTime = (dateStr) => {
    if (!dateStr) return "TBD";
    try {
      const date = new Date(dateStr);
      return format(date, "MMM d, h:mm a");
    } catch {
      return "TBD";
    }
  };

  const getTeamName = (teamId) => {
    const team = teams?.find((t) => t.id === teamId);
    return team ? team.abbreviation : "TBD";
  };

  const columns = [
    {
      key: "game_date",
      header: "Date & Time",
      render: (value) => formatGameTime(value),
    },
    {
      key: "matchup",
      header: "Matchup",
      sortable: false,
      render: (value, game) => (
        <div className="flex items-center justify-center space-x-2">
          <span className="font-medium">{getTeamName(game.away_team_id)}</span>
          <span className="text-muted-foreground">@</span>
          <span className="font-medium">{getTeamName(game.home_team_id)}</span>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (value) => {
        const statusMap = {
          Final: "bg-green-100 text-green-800",
          "In Progress": "bg-blue-100 text-blue-800",
          Upcoming: "bg-gray-100 text-gray-800",
          Postponed: "bg-red-100 text-red-800",
        };

        const className = statusMap[value] || "bg-gray-100 text-gray-800";

        return (
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${className}`}
          >
            {value || "Unknown"}
          </span>
        );
      },
    },
    {
      key: "score",
      header: "Score",
      sortable: false,
      render: (value, game) => {
        if (
          game.status === "Final" &&
          game.away_team_score !== null &&
          game.home_team_score !== null
        ) {
          return (
            <div className="text-center">
              <span className="font-medium">
                {game.away_team_score} - {game.home_team_score}
              </span>
            </div>
          );
        }
        return <span className="text-muted-foreground">-</span>;
      },
    },
    {
      key: "actions",
      header: "",
      sortable: false,
      render: (value, game) => (
        <Link
          to={`/games/${game.id}`}
          className="text-primary hover:underline text-sm"
        >
          View Details
        </Link>
      ),
    },
  ];

  // Filter to only show completed and in-progress games
  const filteredGames =
    games?.filter(
      (game) => game.status === "Final" || game.status === "In Progress",
    ) || [];

  // Sort by most recent first
  const sortedGames = [...filteredGames].sort((a, b) => {
    const dateA = new Date(a.game_date);
    const dateB = new Date(b.game_date);
    return dateB - dateA;
  });

  if (gamesError) {
    return (
      <div className="flex items-center justify-center h-64" role="alert">
        <div className="text-center p-6 max-w-md">
          <div className="text-destructive text-xl mb-2">🏀</div>
          <h2 className="text-lg font-semibold text-destructive mb-2">
            Failed to load games
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
            {gamesError.message}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            aria-label="Retry loading games"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">NBA Games</h1>
          <p className="text-muted-foreground">
            Completed and in-progress games • Click to view game details
          </p>
        </div>
        {sortedGames && sortedGames.length > 0 && (
          <div className="text-sm text-muted-foreground" aria-live="polite">
            {sortedGames.length} games
          </div>
        )}
      </div>

      <SimpleTable
        data={sortedGames}
        columns={columns}
        loading={gamesLoading}
        emptyMessage="No games found"
        onRowClick={(game) => {
          optimizedNavigate(navigate, `/games/${game.id}`);
        }}
        mobileBreakpoint="md"
        className="shadow-sm"
        aria-label="NBA games table"
      />
    </div>
  );
};

export default GamesPage;
