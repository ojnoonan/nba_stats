import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import {
  fetchAdminStatus,
  triggerFullUpdate,
  triggerComponentUpdate,
  cancelAdminUpdate,
} from "../services/api";
import { Button } from "../components/ui/button";
import { LoadingSpinner } from "../components/ui/loading-spinner";

export default function AdminPage() {
  const queryClient = useQueryClient();

  // Reasonable status polling to avoid rate limits
  const {
    data: status,
    isLoading: isLoadingStatus,
    error: statusError,
  } = useQuery({
    queryKey: ["adminStatus"],
    queryFn: fetchAdminStatus,
    refetchInterval: (data) => (data?.is_updating ? 3000 : 10000), // Poll every 3s during updates, 10s otherwise
    staleTime: (data) => (data?.is_updating ? 1000 : 5000), // Less aggressive stale time
    refetchOnReconnect: true,
    refetchOnWindowFocus: true,
    retry: 3,
  });

  const fullUpdateMutation = useMutation({
    mutationFn: triggerFullUpdate,
    onMutate: async () => {
      await queryClient.cancelQueries(["adminStatus"]);
      const previousStatus = queryClient.getQueryData(["adminStatus"]);

      // Update the status optimistically but keep other properties
      queryClient.setQueryData(["adminStatus"], (old) => ({
        ...old,
        is_updating: true,
        current_phase: "initiating_full_update",
        components: old?.components
          ? {
              ...old.components,
              ["initiating_full_update"]: {
                ...(old.components["initiating_full_update"] || {}),
                updated: false,
              },
            }
          : {},
      }));
      return { previousStatus };
    },
    onError: (err, vars, context) => {
      queryClient.setQueryData(["adminStatus"], context.previousStatus);
      console.error("Failed to start full update:", err);
    },
    onSuccess: () => {
      // After successful trigger, let the polling handle the updates
      queryClient.invalidateQueries(["adminStatus"]);
    },
  });

  const componentUpdateMutation = useMutation({
    mutationFn: triggerComponentUpdate,
    onMutate: async (component) => {
      await queryClient.cancelQueries(["adminStatus"]);
      const previousStatus = queryClient.getQueryData(["adminStatus"]);

      // Update the status optimistically but keep other properties
      queryClient.setQueryData(["adminStatus"], (old) => ({
        ...old,
        is_updating: true,
        current_phase: component,
        components: old?.components
          ? {
              ...old.components,
              [component]: {
                ...(old.components[component] || {}),
                updated: false,
              },
            }
          : {},
      }));
      return { previousStatus };
    },
    onError: (err, vars, context) => {
      queryClient.setQueryData(["adminStatus"], context.previousStatus);
      console.error("Failed to start component update:", err);
    },
    onSuccess: () => {
      // After successful trigger, let the polling handle the updates
      queryClient.invalidateQueries(["adminStatus"]);
    },
  });

  const cancelUpdateMutation = useMutation({
    mutationFn: cancelAdminUpdate,
    onMutate: async () => {
      const previousStatus = queryClient.getQueryData(["adminStatus"]);

      // Update the status optimistically but keep other properties
      queryClient.setQueryData(["adminStatus"], (old) => ({
        ...old,
        cancellation_requested: true,
      }));
      return { previousStatus };
    },
    onError: (err, vars, context) => {
      queryClient.setQueryData(["adminStatus"], context.previousStatus);
      console.error("Failed to cancel update:", err);
    },
    onSuccess: () => {
      // After successful cancellation, let the polling handle the updates
      queryClient.invalidateQueries(["adminStatus"]);
    },
  });

  // Show loading state
  if (isLoadingStatus) {
    return (
      <div className="p-4 container mx-auto flex items-center gap-2">
        <LoadingSpinner size="small" />
        <span>Loading Admin Dashboard...</span>
      </div>
    );
  }

  // Show error state
  if (statusError) {
    return (
      <div className="p-4 container mx-auto">
        <div className="p-4 text-red-500 bg-red-100 rounded-lg">
          <h2 className="font-bold mb-2">Error loading admin status</h2>
          <p>{statusError.message}</p>
          <button
            onClick={() => queryClient.invalidateQueries(["adminStatus"])}
            className="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const isOverallUpdating = status?.is_updating;
  const currentPhase = status?.current_phase;
  const components = status?.components || {};
  const isCancellationRequested = status?.cancellation_requested;

  const handleCancel = () => {
    if (!isCancellationRequested) {
      cancelUpdateMutation.mutate();
    }
  };

  return (
    <div className="p-4 container mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-center">Admin Dashboard</h1>

      <div className="mb-10 p-6 border rounded-lg shadow-md bg-card">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-4">
          <h2 className="text-2xl font-semibold">Full Update</h2>
          <div className="flex gap-2">
            <Button
              onClick={() =>
                !isCancellationRequested && fullUpdateMutation.mutate()
              }
              disabled={isOverallUpdating || isCancellationRequested}
              variant={isOverallUpdating ? "destructive" : "default"}
              className={`px-4 py-2 ${isOverallUpdating ? "bg-yellow-500 hover:bg-yellow-600" : "bg-blue-500 hover:bg-blue-600"}`}
            >
              {isOverallUpdating && (
                <LoadingSpinner size="small" className="mr-2" />
              )}
              {isOverallUpdating
                ? `Updating ${currentPhase || "All"}...`
                : "Update All Data"}
            </Button>
            {isOverallUpdating && (
              <Button
                onClick={handleCancel}
                disabled={isCancellationRequested}
                variant="destructive"
                className="bg-red-500 hover:bg-red-600 disabled:opacity-50"
              >
                {isCancellationRequested ? "Cancelling..." : "Cancel Update"}
              </Button>
            )}
          </div>
        </div>

        {isOverallUpdating && (
          <div className="text-sm text-muted-foreground mb-2">
            Current update phase:{" "}
            <span className="font-semibold text-primary">
              {currentPhase === "cleanup"
                ? "Preparing update..."
                : currentPhase === "initiating_full_update"
                  ? "Initiating full update..."
                  : currentPhase === "teams"
                    ? "Updating Teams"
                    : currentPhase === "players"
                      ? "Updating Players"
                      : currentPhase === "games"
                        ? "Updating Games"
                        : currentPhase || "Preparing..."}
            </span>
            {isCancellationRequested && (
              <span className="ml-2 text-yellow-500">
                (Cancellation requested...)
              </span>
            )}
            {status?.current_detail && (
              <div className="mt-1 text-xs text-muted-foreground">
                {status.current_detail}
              </div>
            )}
            {currentPhase && components[currentPhase]?.percent_complete > 0 && (
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                <div
                  className="bg-blue-600 h-2.5 rounded-full"
                  style={{
                    width: `${components[currentPhase].percent_complete}%`,
                  }}
                ></div>
              </div>
            )}
          </div>
        )}

        <div className="text-sm text-muted-foreground">
          Last successful update:{" "}
          {status?.last_successful_update
            ? format(
                new Date(status.last_successful_update),
                "MMM d, yyyy, h:mm a",
              )
            : "Never"}
        </div>
        {status?.next_scheduled_update && (
          <div className="text-sm text-muted-foreground">
            Next scheduled update:{" "}
            {format(
              new Date(status.next_scheduled_update),
              "MMM d, yyyy, h:mm a",
            )}
          </div>
        )}
        {status?.last_error && (
          <div className="mt-2 text-sm text-red-500 bg-red-100 p-2 rounded-md">
            <strong>Last Error:</strong> {status.last_error} (
            {status.last_error_time
              ? new Date(status.last_error_time).toLocaleString()
              : "N/A"}
            )
          </div>
        )}
      </div>

      <div className="space-y-6">
        <h2 className="text-2xl font-semibold mb-6 text-center">
          Individual Components
        </h2>

        {Object.entries(components).map(([component, details]) => {
          const isComponentUpdating =
            isOverallUpdating && currentPhase === component;
          return (
            <div
              key={component}
              className="p-6 border rounded-lg shadow-md bg-card"
            >
              <div className="flex flex-col sm:flex-row items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-xl font-medium capitalize mb-2 sm:mb-0">
                    {component}
                  </h3>
                  {isComponentUpdating && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                      <LoadingSpinner size="small" className="mr-1" />
                      Current Phase
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={() =>
                      !isCancellationRequested &&
                      componentUpdateMutation.mutate(component)
                    }
                    disabled={isOverallUpdating || isCancellationRequested}
                    variant={isComponentUpdating ? "destructive" : "default"}
                    className={`px-3 py-1 ${isComponentUpdating ? "bg-yellow-500 hover:bg-yellow-600" : "bg-blue-500 hover:bg-blue-600"}`}
                  >
                    {isComponentUpdating && (
                      <LoadingSpinner size="small" className="mr-2" />
                    )}
                    {isComponentUpdating
                      ? "Updating..."
                      : `Update ${component}`}
                  </Button>
                  {isComponentUpdating && (
                    <Button
                      onClick={handleCancel}
                      disabled={isCancellationRequested}
                      variant="destructive"
                      className="bg-red-500 hover:bg-red-600 disabled:opacity-50"
                    >
                      {isCancellationRequested
                        ? "Cancelling..."
                        : "Cancel Update"}
                    </Button>
                  )}
                </div>
              </div>

              <div className="text-sm mb-2">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span>Status:</span>
                    <span
                      className={`font-medium ${details.updated ? "text-green-500" : "text-yellow-600"}`}
                    >
                      {details.updated
                        ? "Updated"
                        : isComponentUpdating
                          ? "Updating..."
                          : "Not Updated"}
                    </span>
                  </div>
                  {details.last_update && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span>Last Updated:</span>
                      <span>
                        {format(
                          new Date(details.last_update),
                          "MMM d, yyyy, h:mm a",
                        )}
                      </span>
                    </div>
                  )}
                  {isComponentUpdating &&
                    typeof details.percent_complete === "number" &&
                    details.percent_complete > 0 && (
                      <div className="mt-2">
                        <div className="text-xs text-muted-foreground mb-1">
                          Progress: {details.percent_complete}%
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${details.percent_complete}%` }}
                          ></div>
                        </div>
                      </div>
                    )}
                </div>
              </div>

              {details.last_error &&
                (!isOverallUpdating || currentPhase !== component) && (
                  <div className="mt-2 text-xs text-red-500 bg-red-100 p-2 rounded-md">
                    Last error for {component}: {details.last_error}
                  </div>
                )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
