import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAdminStatus, triggerFullUpdate, triggerComponentUpdate, cancelAdminUpdate } from '../services/api';
import { Button } from '../components/ui/button';
import { LoadingSpinner } from '../components/ui/loading-spinner';

export default function AdminPage() {
    const queryClient = useQueryClient();
    
    const { data: status, isLoading: isLoadingStatus } = useQuery({
        queryKey: ['adminStatus'],
        queryFn: fetchAdminStatus,
        // Refetch more frequently if updating - use a function to access query data safely
        refetchInterval: (data, query) => (data?.is_updating ? 1000 : 5000),
    });

    const fullUpdateMutation = useMutation({
        mutationFn: triggerFullUpdate,
        onSuccess: () => {
            queryClient.invalidateQueries(['adminStatus']);
        }
    });

    const componentUpdateMutation = useMutation({
        mutationFn: triggerComponentUpdate,
        onSuccess: () => {
            queryClient.invalidateQueries(['adminStatus']);
        }
    });

    const cancelUpdateMutation = useMutation({
        mutationFn: cancelAdminUpdate,
        onSuccess: () => {
            queryClient.invalidateQueries(['adminStatus']);
        }
    });

    if (isLoadingStatus) {
        return <div className="p-4 container mx-auto"><LoadingSpinner /> Loading Admin Dashboard...</div>;
    }

    const isOverallUpdating = status?.is_updating;
    const currentPhase = status?.current_phase;
    const components = status?.components || {};

    const handleCancel = () => {
        cancelUpdateMutation.mutate();
    };

    return (
        <div className="p-4 container mx-auto">
            <h1 className="text-3xl font-bold mb-8 text-center">Admin Dashboard</h1>
            
            <div className="mb-10 p-6 border rounded-lg shadow-md bg-card">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-4">
                    <h2 className="text-2xl font-semibold">Full Update</h2>
                    <div className="flex gap-2">
                        <Button
                            onClick={() => fullUpdateMutation.mutate()}
                            disabled={isOverallUpdating}
                            variant={isOverallUpdating && (currentPhase === 'teams' || currentPhase === 'players' || currentPhase === 'games' || !currentPhase) ? "destructive" : "default"}
                            className={`px-4 py-2 ${isOverallUpdating && (currentPhase === 'teams' || currentPhase === 'players' || currentPhase === 'games' || !currentPhase) ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-blue-500 hover:bg-blue-600'}`}
                        >
                            {isOverallUpdating && (currentPhase === 'teams' || currentPhase === 'players' || currentPhase === 'games' || !currentPhase) ? <LoadingSpinner size="small" className="mr-2" /> : null}
                            {isOverallUpdating && (currentPhase === 'teams' || currentPhase === 'players' || currentPhase === 'games' || !currentPhase) ? `Updating ${currentPhase || 'All'}...` : 'Update All Data'}
                        </Button>
                        {isOverallUpdating && (
                            <Button
                                onClick={handleCancel}
                                variant="destructive"
                                className="bg-red-500 hover:bg-red-600"
                            >
                                Cancel Update
                            </Button>
                        )}
                    </div>
                </div>
                
                {isOverallUpdating && currentPhase && (
                    <div className="text-sm text-muted-foreground mb-2">
                        Current update phase: <span className="font-semibold text-primary">{currentPhase}</span>
                    </div>
                )}

                {status?.last_update && (
                    <div className="text-sm text-muted-foreground">
                        Last successful update: {new Date(status.last_update).toLocaleString()}
                    </div>
                )}
                 {status?.last_error && (
                    <div className="mt-2 text-sm text-red-500 bg-red-100 p-2 rounded-md">
                        <strong>Last Error:</strong> {status.last_error} ({status.last_error_time ? new Date(status.last_error_time).toLocaleString() : 'N/A'})
                    </div>
                )}
            </div>

            <div className="space-y-6">
                <h2 className="text-2xl font-semibold mb-6 text-center">Individual Components</h2>
                
                {Object.entries(components).map(([component, details]) => {
                    const isComponentUpdating = isOverallUpdating && currentPhase === component;
                    return (
                        <div key={component} className="p-6 border rounded-lg shadow-md bg-card">
                            <div className="flex flex-col sm:flex-row items-center justify-between mb-4">
                                <h3 className="text-xl font-medium capitalize mb-2 sm:mb-0">{component}</h3>
                                <div className="flex gap-2">
                                    <Button
                                        onClick={() => componentUpdateMutation.mutate(component)}
                                        disabled={isOverallUpdating}
                                        variant={isComponentUpdating ? "destructive" : "default"}
                                        className={`px-3 py-1 ${isComponentUpdating ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-blue-500 hover:bg-blue-600'}`}
                                    >
                                        {isComponentUpdating ? <LoadingSpinner size="small" className="mr-2" /> : null}
                                        {isComponentUpdating ? `Updating...` : `Update ${component}`}
                                    </Button>
                                    {isComponentUpdating && (
                                        <Button
                                            onClick={handleCancel}
                                            variant="destructive"
                                            className="bg-red-500 hover:bg-red-600"
                                        >
                                            Cancel Update
                                        </Button>
                                    )}
                                </div>
                            </div>
                            
                            <div className="text-sm mb-2">
                                <div className="flex items-center gap-2">
                                    <span>Status:</span>
                                    <span className={`font-medium ${details.updated ? 'text-green-500' : 'text-yellow-600'}`}>
                                        {details.updated ? 'Updated' : (isComponentUpdating ? 'Updating...' : 'Not Updated')}
                                    </span>
                                </div>
                            </div>
                            
                            {details.last_error && (!isOverallUpdating || currentPhase !== component) && (
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
