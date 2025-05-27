import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { format, isToday, isTomorrow, addDays } from "date-fns";
import { fetchGames, fetchTeams } from "../services/api";
import { LoadingSpinner } from "../components/ui/loading-spinner";
import { SimpleTable } from "../components/simple/SimpleTable";

const UpcomingGamesPage = () => {
  const {
    data: games,
    isLoading: gamesLoading,
    error: gamesError,
  } = useQuery({
    queryKey: ["games", "upcoming"],
    queryFn: () => fetchGames(null, "Upcoming"),
  });

  const { data: teams } = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const formatGameTime = (dateStr) => {
    if (!dateStr) return "TBD";
    try {
      const date = new Date(dateStr);
      const time = format(date, "h:mm a");

      if (isToday(date)) {
        return `Today, ${time}`;
      } else if (isTomorrow(date)) {
        return `Tomorrow, ${time}`;
      } else {
        return format(date, "MMM d, h:mm a");
      }
    } catch {
      return "TBD";
    }
  };

  const getTeamName = (teamId) => {
    const team = teams?.find((t) => t.id === teamId);
    return team ? team.abbreviation : "TBD";
  };

  const getDaysUntil = (dateStr) => {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      const today = new Date();
      const diffTime = date - today;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      return diffDays;
    } catch {
      return null;
    }
  };

  const columns = [
    {
      key: "game_date",
      header: "When",
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
      key: "countdown",
      header: "Days Until",
      render: (value, game) => {
        const days = getDaysUntil(game.game_date);
        if (days === null) return "-";
        if (days === 0) return "Today";
        if (days === 1) return "Tomorrow";
        return `${days} days`;
      },
    },
    {
      key: "status",
      header: "Status",
      render: (value) => (
        <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {value || "Scheduled"}
        </span>
      ),
    },
  ];

  // Filter to only show upcoming games
  const upcomingGames =
    games?.filter(
      (game) => game.status === "Upcoming" || game.status === "Scheduled",
    ) || [];

  // Sort by date (earliest first)
  const sortedGames = [...upcomingGames].sort((a, b) => {
    const dateA = new Date(a.game_date);
    const dateB = new Date(b.game_date);
    return dateA - dateB;
  });

  if (gamesError) {
    return (
      <div className="flex items-center justify-center h-64" role="alert">
        <div className="text-center p-6 max-w-md">
          <div className="text-destructive text-xl mb-2">📅</div>
          <h2 className="text-lg font-semibold text-destructive mb-2">
            Failed to load upcoming games
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
            {gamesError.message}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            aria-label="Retry loading upcoming games"
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
          <h1 className="text-3xl font-bold">Upcoming Games</h1>
          <p className="text-muted-foreground">
            Scheduled NBA games • Check back for updates
          </p>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card p-4 rounded-lg border">
          <div className="text-sm text-muted-foreground">Total Upcoming</div>
          <div className="text-2xl font-bold">{sortedGames.length}</div>
        </div>
        <div className="bg-card p-4 rounded-lg border">
          <div className="text-sm text-muted-foreground">Today</div>
          <div className="text-2xl font-bold">
            {sortedGames.filter((g) => getDaysUntil(g.game_date) === 0).length}
          </div>
        </div>
        <div className="bg-card p-4 rounded-lg border">
          <div className="text-sm text-muted-foreground">This Week</div>
          <div className="text-2xl font-bold">
            {
              sortedGames.filter((g) => {
                const days = getDaysUntil(g.game_date);
                return days !== null && days >= 0 && days <= 7;
              }).length
            }
          </div>
        </div>
      </div>

      <SimpleTable
        data={sortedGames}
        columns={columns}
        loading={gamesLoading}
        emptyMessage="No upcoming games scheduled"
        mobileBreakpoint="md"
        className="shadow-sm"
        aria-label="Upcoming NBA games table"
      />
    </div>
  );
};

export default UpcomingGamesPage;
