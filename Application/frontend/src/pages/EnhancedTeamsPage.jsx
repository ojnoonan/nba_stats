import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  fetchTeams,
  fetchPlayers,
  fetchGames,
  triggerTeamsUpdate,
} from "../services/api";
import { DataTable } from "../components/shared";
import TeamExpansion from "../components/pages/Teams/TeamExpansion";
import { useTableExpansion } from "../hooks/useTableExpansion";
import { HeaderTooltip } from "../components/shared/Tooltips";

/**
 * Enhanced Teams Page with advanced DataTable features
 * Demonstrates Phase 3 UI/UX enhancements including:
 * - Advanced table features (search, filtering, sorting, export)
 * - Responsive design with mobile cards
 * - Expandable content with team details
 * - Navigation integration
 */
const EnhancedTeamsPage = () => {
  const [selectedTeamId, setSelectedTeamId] = useState(null);

  // Table expansion management with URL persistence
  const {
    expandedRows,
    isExpanded,
    toggleExpansion,
    openInPage,
    closeExpansion,
  } = useTableExpansion("teams");

  // Fetch teams data
  const {
    data: teams = [],
    isLoading: teamsLoading,
    error: teamsError,
    refetch: refetchTeams,
    isFetching: isRefetching,
  } = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  // Fetch expanded team details
  const { data: teamPlayers } = useQuery({
    queryKey: ["players", selectedTeamId],
    queryFn: () => fetchPlayers({ team_id: selectedTeamId }),
    enabled: !!selectedTeamId,
  });

  const { data: teamGames } = useQuery({
    queryKey: ["games", selectedTeamId],
    queryFn: () => fetchGames({ team_id: selectedTeamId }),
    enabled: !!selectedTeamId,
  });

  // Column definitions with tooltips and responsive priorities
  const columns = [
    {
      id: "logo",
      header: "Logo",
      accessorKey: "logo_url",
      responsivePriority: "high",
      cell: ({ getValue, row }) => (
        <div className="flex items-center space-x-2">
          {getValue() && (
            <img
              src={getValue()}
              alt={`${row.original.name} logo`}
              className="w-8 h-8 object-contain"
              onError={(e) => {
                e.target.style.display = "none";
              }}
            />
          )}
        </div>
      ),
    },
    {
      id: "name",
      header: (
        <HeaderTooltip content="Complete team name including city and nickname">
          Team Name
        </HeaderTooltip>
      ),
      accessorKey: "name",
      responsivePriority: "high",
      cell: ({ getValue, row }) => (
        <div className="font-medium">
          <div className="text-sm font-semibold">{getValue()}</div>
          <div className="text-xs text-muted-foreground">
            {row.original.abbreviation}
          </div>
        </div>
      ),
    },
    {
      id: "conference",
      header: (
        <HeaderTooltip content="Eastern or Western Conference">
          Conference
        </HeaderTooltip>
      ),
      accessorKey: "conference",
      responsivePriority: "medium",
      cell: ({ getValue }) => (
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            getValue() === "East"
              ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
              : "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200"
          }`}
        >
          {getValue()}
        </span>
      ),
    },
    {
      id: "division",
      header: (
        <HeaderTooltip content="Division within the conference (Atlantic, Central, Southeast, etc.)">
          Division
        </HeaderTooltip>
      ),
      accessorKey: "division",
      responsivePriority: "low",
      cell: ({ getValue }) => (
        <span className="text-sm text-muted-foreground">{getValue()}</span>
      ),
    },
    {
      id: "founded",
      header: (
        <HeaderTooltip content="Year the team was established">
          Founded
        </HeaderTooltip>
      ),
      accessorKey: "founded",
      responsivePriority: "lowest",
      cell: ({ getValue }) => getValue() || "N/A",
    },
    {
      id: "actions",
      header: "Actions",
      responsivePriority: "high",
      cell: ({ row }) => (
        <div className="flex items-center space-x-2">
          <button
            onClick={() =>
              openInPage(row.original.team_id, `/teams/${row.original.team_id}`)
            }
            className="text-xs px-2 py-1 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            View Details
          </button>
          <button
            onClick={() => {
              setSelectedTeamId(row.original.team_id);
              toggleExpansion(row.original.team_id);
            }}
            className="text-xs px-2 py-1 bg-secondary text-secondary-foreground rounded hover:bg-secondary/90"
          >
            {isExpanded(row.original.team_id) ? "Collapse" : "Expand"}
          </button>
        </div>
      ),
    },
  ];

  // Handle team row expansion
  const handleRowExpansion = (team, expanded) => {
    if (expanded) {
      setSelectedTeamId(team.team_id);
    } else {
      setSelectedTeamId(null);
    }
  };

  // Render expanded team content
  const renderExpandedContent = (team) => (
    <TeamExpansion
      team={team}
      players={teamPlayers}
      games={teamGames}
      onViewTeam={() => openInPage(team.team_id, `/teams/${team.team_id}`)}
    />
  );

  // Handle data update
  const handleUpdate = async () => {
    try {
      await triggerTeamsUpdate();
      refetchTeams();
    } catch (error) {
      console.error("Failed to update teams:", error);
    }
  };

  if (teamsError) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">
            Error Loading Teams
          </h1>
          <p className="text-muted-foreground mb-4">{teamsError.message}</p>
          <button
            onClick={() => refetchTeams()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Enhanced Teams</h1>
          <p className="text-muted-foreground">
            Explore all 30 NBA teams with enhanced features and advanced data
            visualization
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Link
            to="/players"
            className="px-4 py-2 text-sm bg-secondary text-secondary-foreground rounded hover:bg-secondary/90"
          >
            View Players
          </Link>
          <Link
            to="/games"
            className="px-4 py-2 text-sm bg-secondary text-secondary-foreground rounded hover:bg-secondary/90"
          >
            View Games
          </Link>
          <button
            onClick={handleUpdate}
            disabled={isRefetching}
            className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
          >
            {isRefetching ? "Updating..." : "Update Data"}
          </button>
        </div>
      </div>

      {/* Enhanced DataTable with all advanced features */}
      <DataTable
        columns={columns}
        data={teams}
        loading={teamsLoading}
        emptyMessage="No teams found"
        // Advanced Features
        enableAdvancedFeatures={true}
        enableSearch={true}
        enableFiltering={true}
        enableColumnVisibility={true}
        enableExport={true}
        enableMultiSort={true}
        // Expandable Content
        expandable={true}
        onRowClick={handleRowExpansion}
        renderExpanded={renderExpandedContent}
        getRowId={(row) => row.team_id}
        // Responsive Design
        responsive={true}
        enableMobileCards={true}
        mobileBreakpoint="sm"
        // Table Configuration
        title="NBA Teams"
        className="shadow-lg"
        searchFields={["name", "conference", "division", "abbreviation"]}
      />

      {/* Additional Features Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
        <div className="bg-card border rounded-lg p-4">
          <h3 className="font-semibold mb-2">🔍 Advanced Search</h3>
          <p>
            Search teams by name, city, conference, or division. Use the search
            bar in the table header.
          </p>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <h3 className="font-semibold mb-2">📱 Mobile Responsive</h3>
          <p>
            Table automatically adapts to mobile screens with card layout and
            priority-based column hiding.
          </p>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <h3 className="font-semibold mb-2">📊 Export Data</h3>
          <p>
            Export filtered data to CSV or JSON format. Use the export button in
            the table actions.
          </p>
        </div>
      </div>
    </div>
  );
};

export default EnhancedTeamsPage;
