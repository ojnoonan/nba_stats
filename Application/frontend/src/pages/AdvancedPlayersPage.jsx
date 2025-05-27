import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  fetchPlayers,
  fetchTeams,
  fetchPlayerStats,
  triggerPlayersUpdate,
} from "../services/api";
import { DataTable } from "../components/shared";
import PlayerExpansion from "../components/pages/Players/PlayerExpansion";
import { useTableExpansion } from "../hooks/useTableExpansion";
import { HeaderTooltip } from "../components/shared/Tooltips";

/**
 * Advanced Players Page with comprehensive DataTable features
 * Demonstrates Phase 3 UI/UX enhancements including:
 * - Advanced table features (search, filtering, sorting, export)
 * - Responsive design with mobile cards
 * - Expandable content with player details
 * - Statistical analysis and filtering
 */
const AdvancedPlayersPage = () => {
  const [selectedPlayerId, setSelectedPlayerId] = useState(null);

  // Table expansion management with URL persistence
  const {
    expandedRows,
    isExpanded,
    toggleExpansion,
    openInPage,
    closeExpansion,
  } = useTableExpansion("players");

  // Fetch players data
  const {
    data: players = [],
    isLoading: playersLoading,
    error: playersError,
    refetch: refetchPlayers,
    isFetching: isRefetching,
  } = useQuery({
    queryKey: ["players"],
    queryFn: () => fetchPlayers(null, true),
  });

  // Fetch teams data for player team names
  const { data: teams = [] } = useQuery({
    queryKey: ["teams"],
    queryFn: fetchTeams,
  });

  // Fetch expanded player details
  const { data: playerStats } = useQuery({
    queryKey: ["playerStats", selectedPlayerId],
    queryFn: () => fetchPlayerStats(selectedPlayerId),
    enabled: !!selectedPlayerId,
  });

  // Helper function to get team name
  const getTeamName = (teamId) => {
    const team = teams.find((t) => t.team_id === teamId);
    return team?.name || "Free Agent";
  };

  // Column definitions with tooltips and responsive priorities
  const columns = [
    {
      id: "headshot",
      header: "Photo",
      accessorKey: "headshot_url",
      responsivePriority: "high",
      cell: ({ getValue, row }) => (
        <div className="flex items-center space-x-2">
          {getValue() ? (
            <img
              src={getValue()}
              alt={`${row.original.full_name} headshot`}
              className="w-10 h-10 rounded-full object-cover"
              onError={(e) => {
                e.target.src = "/default-player.png";
              }}
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
              <span className="text-xs text-gray-500">No Photo</span>
            </div>
          )}
        </div>
      ),
    },
    {
      id: "full_name",
      header: (
        <HeaderTooltip content="Player's complete name as listed in official NBA records">
          Player Name
        </HeaderTooltip>
      ),
      accessorKey: "full_name",
      responsivePriority: "high",
      cell: ({ getValue, row }) => (
        <div className="font-medium">
          <div className="text-sm font-semibold">{getValue()}</div>
          {row.original.jersey_number && (
            <div className="text-xs text-muted-foreground">
              #{row.original.jersey_number}
            </div>
          )}
        </div>
      ),
    },
    {
      id: "team",
      header: (
        <HeaderTooltip content="Current NBA team or Free Agent status">
          Current Team
        </HeaderTooltip>
      ),
      accessorFn: (row) => getTeamName(row.current_team_id),
      responsivePriority: "high",
      cell: ({ getValue, row }) => (
        <div>
          <span
            className={`text-sm ${getValue() === "Free Agent" ? "text-orange-600 dark:text-orange-400" : ""}`}
          >
            {getValue()}
          </span>
          {row.original.is_traded && (
            <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              Recently Traded
            </div>
          )}
        </div>
      ),
    },
    {
      id: "position",
      header: (
        <HeaderTooltip content="Primary playing position (PG, SG, SF, PF, C)">
          Position
        </HeaderTooltip>
      ),
      accessorKey: "position",
      responsivePriority: "medium",
      cell: ({ getValue }) => (
        <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200">
          {getValue() || "N/A"}
        </span>
      ),
    },
    {
      id: "points",
      header: (
        <HeaderTooltip content="Points scored per game this season">
          PPG
        </HeaderTooltip>
      ),
      accessorKey: "points",
      responsivePriority: "medium",
      cell: ({ getValue }) => (getValue() || 0).toFixed(1),
    },
    {
      id: "rebounds",
      header: (
        <HeaderTooltip content="Rebounds per game this season">
          RPG
        </HeaderTooltip>
      ),
      accessorKey: "rebounds",
      responsivePriority: "medium",
      cell: ({ getValue }) => (getValue() || 0).toFixed(1),
    },
    {
      id: "assists",
      header: (
        <HeaderTooltip content="Assists per game this season">
          APG
        </HeaderTooltip>
      ),
      accessorKey: "assists",
      responsivePriority: "medium",
      cell: ({ getValue }) => (getValue() || 0).toFixed(1),
    },
    {
      id: "fg_pct",
      header: (
        <HeaderTooltip content="Field goal shooting percentage">
          FG%
        </HeaderTooltip>
      ),
      accessorKey: "fg_pct",
      responsivePriority: "low",
      cell: ({ getValue }) => {
        const pct = getValue();
        return pct ? `${(pct * 100).toFixed(1)}%` : "0.0%";
      },
    },
    {
      id: "minutes",
      header: (
        <HeaderTooltip content="Minutes played per game">MPG</HeaderTooltip>
      ),
      accessorKey: "minutes",
      responsivePriority: "low",
      cell: ({ getValue }) => (getValue() || 0).toFixed(1),
    },
    {
      id: "is_active",
      header: (
        <HeaderTooltip content="Player's current active status">
          Status
        </HeaderTooltip>
      ),
      accessorKey: "is_active",
      responsivePriority: "medium",
      cell: ({ getValue }) => (
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            getValue()
              ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
              : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
          }`}
        >
          {getValue() ? "Active" : "Inactive"}
        </span>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      responsivePriority: "high",
      cell: ({ row }) => (
        <div className="flex items-center space-x-2">
          <button
            onClick={() =>
              openInPage(
                row.original.player_id,
                `/players/${row.original.player_id}`,
              )
            }
            className="text-xs px-2 py-1 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            View Profile
          </button>
          <button
            onClick={() => {
              setSelectedPlayerId(row.original.player_id);
              toggleExpansion(row.original.player_id);
            }}
            className="text-xs px-2 py-1 bg-secondary text-secondary-foreground rounded hover:bg-secondary/90"
          >
            {isExpanded(row.original.player_id) ? "Collapse" : "Expand"}
          </button>
        </div>
      ),
    },
  ];

  // Handle player row expansion
  const handleRowExpansion = (player, expanded) => {
    if (expanded) {
      setSelectedPlayerId(player.player_id);
    } else {
      setSelectedPlayerId(null);
    }
  };

  // Render expanded player content
  const renderExpandedContent = (player) => (
    <PlayerExpansion
      player={player}
      stats={playerStats}
      onViewPlayer={() =>
        openInPage(player.player_id, `/players/${player.player_id}`)
      }
    />
  );

  // Handle data update
  const handleUpdate = async () => {
    try {
      await triggerPlayersUpdate();
      refetchPlayers();
    } catch (error) {
      console.error("Failed to update players:", error);
    }
  };

  if (playersError) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">
            Error Loading Players
          </h1>
          <p className="text-muted-foreground mb-4">{playersError.message}</p>
          <button
            onClick={() => refetchPlayers()}
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
          <h1 className="text-3xl font-bold">Advanced Players</h1>
          <p className="text-muted-foreground">
            Comprehensive player database with advanced filtering, statistics,
            and analytics
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Link
            to="/teams"
            className="px-4 py-2 text-sm bg-secondary text-secondary-foreground rounded hover:bg-secondary/90"
          >
            View Teams
          </Link>
          <Link
            to="/enhanced-teams"
            className="px-4 py-2 text-sm bg-secondary text-secondary-foreground rounded hover:bg-secondary/90"
          >
            Enhanced Teams
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
        data={players}
        loading={playersLoading}
        emptyMessage="No players found"
        // Advanced Features
        enableAdvancedFeatures={true}
        enableSearch={true}
        enableFiltering={true}
        enableColumnVisibility={true}
        enableExport={true}
        enableSorting={true}
        enableMultiSort={true}
        // Expandable Content
        expandable={true}
        onRowClick={handleRowExpansion}
        renderExpanded={renderExpandedContent}
        getRowId={(row) => row.player_id}
        // Responsive Design
        responsive={true}
        enableMobileCards={true}
        mobileBreakpoint="sm"
        // Table Configuration
        title="NBA Players"
        className="shadow-lg"
        searchFields={["full_name", "position", "current_team_id"]}
        // Advanced Filtering Options
        enableAdvancedFilters={true}
        filterOptions={[
          {
            key: "is_active",
            label: "Status",
            type: "select",
            options: [
              { value: true, label: "Active" },
              { value: false, label: "Inactive" },
            ],
          },
          {
            key: "position",
            label: "Position",
            type: "select",
            options: [
              { value: "PG", label: "Point Guard" },
              { value: "SG", label: "Shooting Guard" },
              { value: "SF", label: "Small Forward" },
              { value: "PF", label: "Power Forward" },
              { value: "C", label: "Center" },
            ],
          },
          {
            key: "is_traded",
            label: "Trade Status",
            type: "select",
            options: [
              { value: true, label: "Recently Traded" },
              { value: false, label: "Not Traded" },
            ],
          },
        ]}
      />

      {/* Additional Features Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
        <div className="bg-card border rounded-lg p-4">
          <h3 className="font-semibold mb-2">🔍 Advanced Search</h3>
          <p>
            Search players by name, position, or team. Use filters to narrow
            down results by status, position, or trade history.
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
            Export filtered player data to CSV or JSON format. Use the export
            button in the table actions.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdvancedPlayersPage;
