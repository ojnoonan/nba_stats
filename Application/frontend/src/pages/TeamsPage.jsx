import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { fetchTeams } from "../services/api";
import { LoadingSpinner } from "../components/ui/loading-spinner";
import { SimpleTable } from "../components/simple/SimpleTable";
import { useUserPreferences } from "../utils/userPreferences";
import { optimizedNavigate } from "../utils/performance";

const TeamsPage = () => {
  const { preferences } = useUserPreferences();
  const navigate = useNavigate();

  const {
    data: teams,
    isLoading: teamsLoading,
    error: teamsError,
  } = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  const columns = [
    {
      key: "logo_and_name",
      header: "Team",
      sortable: false,
      render: (value, team) => (
        <div className="flex items-center space-x-3">
          {preferences.showTeamLogos && team.logo_url && (
            <img
              src={team.logo_url}
              alt={`${team.name} logo`}
              className="h-8 w-8 object-contain"
              onError={(e) => {
                e.target.style.display = "none";
              }}
            />
          )}
          <div>
            <Link
              to={`/teams/${team.id}`}
              className="font-medium text-primary hover:underline"
            >
              {team.name}
            </Link>
            <div className="text-sm text-muted-foreground">
              {team.abbreviation}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: "conference",
      header: "Conference",
    },
    {
      key: "division",
      header: "Division",
    },
    {
      key: "wins",
      header: "Wins",
      render: (value) => value || 0,
    },
    {
      key: "losses",
      header: "Losses",
      render: (value) => value || 0,
    },
    {
      key: "win_percentage",
      header: "Win %",
      render: (value, team) => {
        const wins = team.wins || 0;
        const losses = team.losses || 0;
        const total = wins + losses;
        const percentage =
          total > 0 ? ((wins / total) * 100).toFixed(1) : "0.0";
        return `${percentage}%`;
      },
    },
  ];

  if (teamsError) {
    return (
      <div className="flex items-center justify-center h-64" role="alert">
        <div className="text-center p-6 max-w-md">
          <div className="text-destructive text-xl mb-2">⚠️</div>
          <h2 className="text-lg font-semibold text-destructive mb-2">
            Failed to load teams
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
            {teamsError.message}
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
          <h1 className="text-3xl font-bold">NBA Teams</h1>
          <p className="text-muted-foreground">
            Click on any team to view roster and schedule
          </p>
        </div>
        {teams && teams.length > 0 && (
          <div className="text-sm text-muted-foreground">
            {teams.length} teams
          </div>
        )}
      </div>

      <SimpleTable
        data={teams || []}
        columns={columns}
        loading={teamsLoading}
        emptyMessage="No teams found"
        onRowClick={(team) => {
          // Handle row click navigation with optimization
          optimizedNavigate(navigate, `/teams/${team.id}`);
        }}
        tableId="teams-table"
        mobileBreakpoint="md"
        className="shadow-sm"
      />
    </div>
  );
};

export default TeamsPage;
