import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { fetchTeam, fetchPlayers, fetchGames } from "../services/api";
import { LoadingSpinner } from "../components/ui/loading-spinner";
import { SimpleTable } from "../components/simple/SimpleTable";
import { format } from "date-fns";

const TeamDetailPage = () => {
  const { id } = useParams();

  const {
    data: team,
    isLoading: teamLoading,
    error: teamError,
  } = useQuery({
    queryKey: ["team", id],
    queryFn: () => fetchTeam(id),
    enabled: !!id,
  });

  const { data: players } = useQuery({
    queryKey: ["players", "team", id],
    queryFn: () => fetchPlayers({ team_id: id }),
    enabled: !!id,
  });

  const { data: games } = useQuery({
    queryKey: ["games", "team", id],
    queryFn: () => fetchGames({ team_id: id }),
    enabled: !!id,
  });

  const rosterColumns = [
    {
      key: "name",
      header: "Player",
      render: (value, player) => (
        <Link
          to={`/players/${player.id}`}
          className="font-medium text-primary hover:underline"
        >
          {value}
        </Link>
      ),
    },
    {
      key: "position",
      header: "Position",
    },
    {
      key: "height",
      header: "Height",
    },
    {
      key: "weight",
      header: "Weight",
      render: (value) => (value ? `${value} lbs` : "N/A"),
    },
    {
      key: "age",
      header: "Age",
    },
  ];

  const gameColumns = [
    {
      key: "date",
      header: "Date",
      render: (value) => format(new Date(value), "MMM d"),
    },
    {
      key: "opponent",
      header: "Opponent",
      render: (value, game) => {
        const isHome = game.home_team_id === team?.id;
        const opponent = isHome ? game.away_team_name : game.home_team_name;
        return (
          <div>
            <span className="text-sm text-muted-foreground">
              {isHome ? "vs" : "@"}
            </span>{" "}
            {opponent}
          </div>
        );
      },
    },
    {
      key: "result",
      header: "Result",
      render: (value, game) => {
        if (game.status !== "Final") {
          return <span className="text-muted-foreground">TBD</span>;
        }

        const isHome = game.home_team_id === team?.id;
        const teamScore = isHome ? game.home_team_score : game.away_team_score;
        const opponentScore = isHome
          ? game.away_team_score
          : game.home_team_score;
        const won = teamScore > opponentScore;

        return (
          <div className={won ? "text-green-600" : "text-red-600"}>
            <span className="font-medium">{won ? "W" : "L"}</span>{" "}
            <span className="text-sm">
              {teamScore}-{opponentScore}
            </span>
          </div>
        );
      },
    },
  ];

  if (teamLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (teamError || !team) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-destructive mb-2">Team not found</p>
          <Link to="/teams" className="text-primary hover:underline">
            ← Back to all teams
          </Link>
        </div>
      </div>
    );
  }

  const recentGames =
    games
      ?.filter((g) => g.status === "Final")
      .sort((a, b) => new Date(b.date) - new Date(a.date))
      .slice(0, 10) || [];

  const upcomingGames =
    games
      ?.filter((g) => g.status === "Upcoming")
      .sort((a, b) => new Date(a.date) - new Date(b.date))
      .slice(0, 5) || [];

  return (
    <div className="space-y-8">
      {/* Team Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link
            to="/teams"
            className="text-sm text-primary hover:underline mb-2 inline-block"
          >
            ← Back to all teams
          </Link>
          <div className="flex items-center space-x-4">
            {team.logo_url && (
              <img
                src={team.logo_url}
                alt={`${team.name} logo`}
                className="w-16 h-16 object-contain"
                onError={(e) => (e.target.style.display = "none")}
              />
            )}
            <div>
              <h1 className="text-3xl font-bold">{team.name}</h1>
              <p className="text-muted-foreground">
                {team.conference} Conference • {team.division} Division
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Team Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-card p-4 rounded-lg border">
          <div className="text-sm text-muted-foreground">Wins</div>
          <div className="text-2xl font-bold">{team.wins || 0}</div>
        </div>
        <div className="bg-card p-4 rounded-lg border">
          <div className="text-sm text-muted-foreground">Losses</div>
          <div className="text-2xl font-bold">{team.losses || 0}</div>
        </div>
        <div className="bg-card p-4 rounded-lg border">
          <div className="text-sm text-muted-foreground">Win %</div>
          <div className="text-2xl font-bold">
            {(() => {
              const wins = team.wins || 0;
              const losses = team.losses || 0;
              const total = wins + losses;
              return total > 0 ? `${((wins / total) * 100).toFixed(1)}%` : "0%";
            })()}
          </div>
        </div>
        <div className="bg-card p-4 rounded-lg border">
          <div className="text-sm text-muted-foreground">Players</div>
          <div className="text-2xl font-bold">{players?.length || 0}</div>
        </div>
      </div>

      {/* Team Roster */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Current Roster</h2>
        <SimpleTable
          data={players || []}
          columns={rosterColumns}
          loading={!players}
          emptyMessage="No roster information available"
        />
      </div>

      {/* Recent Games */}
      {recentGames.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">Recent Games</h2>
          <SimpleTable
            data={recentGames}
            columns={gameColumns}
            emptyMessage="No recent games"
            onRowClick={(game) => {
              window.location.href = `/games/${game.id}`;
            }}
          />
        </div>
      )}

      {/* Upcoming Games */}
      {upcomingGames.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">Upcoming Games</h2>
          <SimpleTable
            data={upcomingGames}
            columns={gameColumns}
            emptyMessage="No upcoming games scheduled"
          />
        </div>
      )}
    </div>
  );
};

export default TeamDetailPage;
