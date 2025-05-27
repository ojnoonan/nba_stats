import React, { useState, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { LoadingSpinner } from "../components/ui/loading-spinner";
import { ErrorBoundary, ApiErrorBoundary } from "../components/error";
import { useApiCall, useBatchApiCalls } from "../hooks/useApiError";
import { useError } from "../contexts/ErrorContext";
import {
  fetchPlayers,
  fetchTeams,
  fetchPlayerStats,
  fetchPlayer,
} from "../services/enhancedApi";

// Component for demonstrating enhanced error handling
const EnhancedPlayersPage = () => {
  const queryClient = useQueryClient();
  const { id } = useParams();
  const { addError, ERROR_TYPES, ERROR_SEVERITIES } = useError();
  const [sorting, setSorting] = useState([]);

  // Using the enhanced API hook for better error handling
  const {
    data: players,
    loading: playersLoading,
    error: playersError,
    execute: loadPlayers,
    retry: retryPlayers,
    attemptCount: playersAttempts,
  } = useApiCall(
    useCallback(() => {
      console.log("Loading players with enhanced error handling");
      return id ? fetchPlayer(id) : fetchPlayers(null, true);
    }, [id]),
    {
      immediate: true,
      retryCount: 3,
      onError: (error) => {
        addError(error, {
          type: ERROR_TYPES.API_ERROR,
          title: "Failed to Load Players",
          message: "Unable to fetch player data. Please try again.",
          context: { playerId: id, operation: "fetchPlayers" },
          actions: [
            {
              label: "Retry",
              handler: retryPlayers,
              icon: () => <span>🔄</span>,
            },
          ],
        });
      },
      onSuccess: (data) => {
        console.log("Players loaded successfully:", data);
      },
    },
  );

  // Batch API calls example
  const {
    results: batchResults,
    loading: batchLoading,
    errors: batchErrors,
    executeAll: loadBatchData,
    executeOne: loadSingleData,
    hasErrors: hasBatchErrors,
  } = useBatchApiCalls(
    {
      teams: fetchTeams,
      playerStats: id ? () => fetchPlayerStats(id) : null,
    },
    {
      onAnyError: (key, error) => {
        addError(error, {
          type: ERROR_TYPES.API_ERROR,
          title: `Failed to Load ${key}`,
          message: `Unable to fetch ${key} data.`,
          context: { operation: key, playerId: id },
          severity: ERROR_SEVERITIES.MEDIUM,
        });
      },
      onAllSuccess: (results) => {
        console.log("All batch data loaded successfully:", results);
      },
    },
  );

  // Custom retry function with error handling
  const handleRetryWithFeedback = useCallback(async () => {
    try {
      await retryPlayers();
      addError(null, {
        type: ERROR_TYPES.API_ERROR,
        title: "Retry Successful",
        message: "Data has been reloaded successfully.",
        severity: ERROR_SEVERITIES.LOW,
        timeout: 3000,
      });
    } catch (error) {
      addError(error, {
        type: ERROR_TYPES.API_ERROR,
        title: "Retry Failed",
        message: "Unable to reload data after multiple attempts.",
        severity: ERROR_SEVERITIES.HIGH,
        context: { retryAttempt: playersAttempts },
      });
    }
  }, [retryPlayers, addError, playersAttempts]);

  // Error state rendering
  if (playersError) {
    return (
      <ApiErrorBoundary
        onRetry={handleRetryWithFeedback}
        fallback={({ error, onRetry, isRetrying }) => (
          <div className="flex items-center justify-center min-h-screen">
            <div className="max-w-md p-6 bg-white rounded-lg shadow-lg">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Unable to Load Players
              </h2>
              <p className="text-gray-600 mb-6">
                {error?.message ||
                  "An unexpected error occurred while loading player data."}
              </p>
              <div className="space-y-3">
                <button
                  onClick={onRetry}
                  disabled={isRetrying}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {isRetrying
                    ? "Retrying..."
                    : `Retry (Attempt ${playersAttempts + 1})`}
                </button>
                <Link
                  to="/"
                  className="block w-full text-center bg-gray-200 text-gray-700 py-2 px-4 rounded hover:bg-gray-300"
                >
                  Go Home
                </Link>
              </div>
              {error?.correlationId && (
                <p className="text-xs text-gray-500 mt-4">
                  Error ID: {error.correlationId}
                </p>
              )}
            </div>
          </div>
        )}
      >
        <div>Error occurred</div>
      </ApiErrorBoundary>
    );
  }

  // Loading state
  if (playersLoading || batchLoading.teams) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <ErrorBoundary name="PlayersPageContent" level="component">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            {id ? "Player Details" : "NBA Players"}
          </h1>

          <div className="flex space-x-2">
            <button
              onClick={() => loadBatchData()}
              disabled={batchLoading.teams}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {batchLoading.teams ? "Loading..." : "Refresh All Data"}
            </button>

            <button
              onClick={handleRetryWithFeedback}
              disabled={playersLoading}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:bg-gray-400"
            >
              {playersLoading ? "Loading..." : "Retry Players"}
            </button>
          </div>
        </div>

        {/* Error Summary */}
        {(hasBatchErrors || playersError) && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h3 className="text-red-800 font-medium mb-2">
              Data Loading Issues
            </h3>
            <ul className="text-red-700 text-sm space-y-1">
              {playersError && (
                <li>• Failed to load players: {playersError.message}</li>
              )}
              {Object.entries(batchErrors).map(([key, error]) => (
                <li key={key}>
                  • Failed to load {key}: {error.message}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Main Content */}
        <ErrorBoundary name="PlayersTable" level="component">
          {players && (
            <div className="bg-white rounded-lg shadow">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-4">
                  {Array.isArray(players)
                    ? `${players.length} Players`
                    : "Player Information"}
                </h2>

                {/* Player Data Display */}
                {Array.isArray(players) ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {players.slice(0, 12).map((player) => (
                      <ErrorBoundary
                        key={player.id}
                        name={`Player-${player.id}`}
                        level="component"
                      >
                        <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                          <h3 className="font-medium text-gray-900">
                            {player.name}
                          </h3>
                          <p className="text-gray-600 text-sm">
                            {player.position}
                          </p>
                          <p className="text-gray-500 text-xs">{player.team}</p>
                          <Link
                            to={`/players/${player.id}`}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            View Details →
                          </Link>
                        </div>
                      </ErrorBoundary>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Name
                        </label>
                        <p className="text-gray-900">{players.name}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Position
                        </label>
                        <p className="text-gray-900">{players.position}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Team
                        </label>
                        <p className="text-gray-900">{players.team}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Jersey
                        </label>
                        <p className="text-gray-900">{players.jersey_number}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </ErrorBoundary>

        {/* Stats Section */}
        <ErrorBoundary name="PlayerStats" level="component">
          {batchResults.playerStats && (
            <div className="mt-8 bg-white rounded-lg shadow">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-4">Statistics</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(batchResults.playerStats).map(
                    ([key, value]) => (
                      <div key={key} className="text-center">
                        <p className="text-2xl font-bold text-blue-600">
                          {value}
                        </p>
                        <p className="text-sm text-gray-600 capitalize">
                          {key.replace("_", " ")}
                        </p>
                      </div>
                    ),
                  )}
                </div>
              </div>
            </div>
          )}
        </ErrorBoundary>

        {/* Teams Section */}
        <ErrorBoundary name="TeamsSection" level="component">
          {batchResults.teams && (
            <div className="mt-8 bg-white rounded-lg shadow">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-4">All Teams</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {batchResults.teams.map((team) => (
                    <Link
                      key={team.id}
                      to={`/teams/${team.id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm p-2 rounded hover:bg-gray-50"
                    >
                      {team.name}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          )}
        </ErrorBoundary>

        {/* Debug Information (Development Only) */}
        {process.env.NODE_ENV === "development" && (
          <div className="mt-8 bg-gray-100 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-2">
              Debug Information
            </h3>
            <div className="text-sm text-gray-700 space-y-1">
              <p>Players Loading: {playersLoading ? "Yes" : "No"}</p>
              <p>Players Attempts: {playersAttempts}</p>
              <p>
                Batch Loading:{" "}
                {
                  Object.entries(batchLoading).filter(([, loading]) => loading)
                    .length
                }{" "}
                active
              </p>
              <p>Batch Errors: {Object.keys(batchErrors).length}</p>
              <p>Has Players Error: {playersError ? "Yes" : "No"}</p>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default EnhancedPlayersPage;
