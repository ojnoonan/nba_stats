import { useQuery } from "@tanstack/react-query";
import { Link, useParams, useNavigate } from "react-router-dom";
import { fetchPlayers, fetchTeams, fetchPlayer } from "../services/api";
import { LoadingSpinner } from "../components/ui/loading-spinner";
import { SimpleTable } from "../components/simple/SimpleTable";
import { useUserPreferences } from "../utils/userPreferences";
import { optimizedNavigate } from "../utils/performance";

const PlayersPage = () => {
  const { id } = useParams();
  const { preferences } = useUserPreferences();
  const navigate = useNavigate();

  // Fetch players data
  const {
    data: players,
    isLoading: playersLoading,
    error: playersError,
  } = useQuery({
    queryKey: ["players", id],
    queryFn: () => {
      return id ? fetchPlayer(id) : fetchPlayers(null, true);
    },
  });

  // Fetch teams data for team names
  const { data: teams } = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  // If viewing a specific player, show player details
  if (id) {
    if (playersLoading) {
      return (
        <div
          className="flex items-center justify-center h-64"
          role="status"
          aria-label="Loading player"
        >
          <LoadingSpinner size="large" />
          <span className="sr-only">Loading player details...</span>
        </div>
      );
    }

    if (playersError || !players) {
      return (
        <div className="flex items-center justify-center h-64" role="alert">
          <div className="text-center p-6 max-w-md">
            <div className="text-destructive text-xl mb-2">👤</div>
            <h2 className="text-lg font-semibold text-destructive mb-2">
              Player not found
            </h2>
            <p className="text-sm text-muted-foreground mb-4">
              {playersError?.message ||
                "The requested player could not be found."}
            </p>
            <Link
              to="/players"
              className="inline-flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            >
              ← Back to all players
            </Link>
          </div>
        </div>
      );
    }

    // Single player view
    const player = Array.isArray(players) ? players[0] : players;
    const team = teams?.find((t) => t.id === player.team_id);

    return (
      <div className="space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <Link
              to="/players"
              className="text-sm text-primary hover:underline mb-2 inline-block"
            >
              ← Back to all players
            </Link>
            <h1 className="text-3xl font-bold">{player.name}</h1>
            <p className="text-muted-foreground">
              {player.position} • {team?.name || "Unknown Team"}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-card p-4 rounded-lg border">
            <div className="text-sm text-muted-foreground">Height</div>
            <div className="text-lg font-semibold">
              {player.height || "N/A"}
            </div>
          </div>
          <div className="bg-card p-4 rounded-lg border">
            <div className="text-sm text-muted-foreground">Weight</div>
            <div className="text-lg font-semibold">
              {player.weight ? `${player.weight} lbs` : "N/A"}
            </div>
          </div>
          <div className="bg-card p-4 rounded-lg border">
            <div className="text-sm text-muted-foreground">Age</div>
            <div className="text-lg font-semibold">{player.age || "N/A"}</div>
          </div>
          <div className="bg-card p-4 rounded-lg border">
            <div className="text-sm text-muted-foreground">Experience</div>
            <div className="text-lg font-semibold">
              {player.years_pro ? `${player.years_pro} years` : "Rookie"}
            </div>
          </div>
        </div>

        {/* Season Stats */}
        <div className="bg-card p-6 rounded-lg border">
          <h2 className="text-xl font-semibold mb-4">Season Stats</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">
                {player.points_per_game || 0}
              </div>
              <div className="text-sm text-muted-foreground">PPG</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {player.rebounds_per_game || 0}
              </div>
              <div className="text-sm text-muted-foreground">RPG</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {player.assists_per_game || 0}
              </div>
              <div className="text-sm text-muted-foreground">APG</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {player.steals_per_game || 0}
              </div>
              <div className="text-sm text-muted-foreground">SPG</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {player.blocks_per_game || 0}
              </div>
              <div className="text-sm text-muted-foreground">BPG</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {player.field_goal_percentage
                  ? `${(player.field_goal_percentage * 100).toFixed(1)}%`
                  : "0%"}
              </div>
              <div className="text-sm text-muted-foreground">FG%</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // All players view
  const columns = [
    {
      key: "name_and_position",
      header: "Player",
      sortable: false,
      render: (value, player) => (
        <div>
          <Link
            to={`/players/${player.id}`}
            className="font-medium text-primary hover:underline"
          >
            {player.name}
          </Link>
          <div className="text-sm text-muted-foreground">
            {player.position || "N/A"}
          </div>
        </div>
      ),
    },
    {
      key: "team_name",
      header: "Team",
      render: (value, player) => {
        const team = teams?.find((t) => t.id === player.team_id);
        return team ? (
          <Link
            to={`/teams/${team.id}`}
            className="text-primary hover:underline"
          >
            {team.abbreviation}
          </Link>
        ) : (
          "Unknown"
        );
      },
    },
    {
      key: "points_per_game",
      header: "PPG",
      render: (value) => (value || 0).toFixed(1),
    },
    {
      key: "rebounds_per_game",
      header: "RPG",
      render: (value) => (value || 0).toFixed(1),
    },
    {
      key: "assists_per_game",
      header: "APG",
      render: (value) => (value || 0).toFixed(1),
    },
    {
      key: "field_goal_percentage",
      header: "FG%",
      render: (value) => (value ? `${(value * 100).toFixed(1)}%` : "0%"),
    },
  ];

  if (playersError) {
    return (
      <div className="flex items-center justify-center h-64" role="alert">
        <div className="text-center p-6 max-w-md">
          <div className="text-destructive text-xl mb-2">⚠️</div>
          <h2 className="text-lg font-semibold text-destructive mb-2">
            Failed to load players
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
            {playersError.message}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
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
          <h1 className="text-3xl font-bold">NBA Players</h1>
          <p className="text-muted-foreground">
            Click on any player to view detailed stats
          </p>
        </div>
        {players && players.length > 0 && (
          <div className="text-sm text-muted-foreground">
            {players.length} players
          </div>
        )}
      </div>

      <SimpleTable
        data={players || []}
        columns={columns}
        loading={playersLoading}
        emptyMessage="No players found"
        onRowClick={(player) => {
          optimizedNavigate(navigate, `/players/${player.id}`);
        }}
        mobileBreakpoint="md"
        className="shadow-sm"
      />
    </div>
  );
};

export default PlayersPage;
