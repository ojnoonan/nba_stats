import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAdminStatus, triggerFullUpdate, triggerComponentUpdate } from '../services/api';

export default function AdminPage() {
    const queryClient = useQueryClient();
    
    const { data: status, isLoading } = useQuery({
        queryKey: ['adminStatus'],
        queryFn: fetchAdminStatus,
        refetchInterval: 5000 // Refetch every 5 seconds while update is in progress
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

    if (isLoading) {
        return <div className="p-4">Loading...</div>;
    }

    const isUpdating = status?.is_updating;
    const components = status?.components || {};

    return (
        <div className="p-4">
            <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>
            
            <div className="mb-8">
                <div className="flex items-center gap-4 mb-4">
                    <h2 className="text-xl font-semibold">Full Update</h2>
                    <button
                        onClick={() => fullUpdateMutation.mutate()}
                        disabled={isUpdating}
                        className={`px-4 py-2 rounded-md ${
                            isUpdating
                                ? 'bg-gray-300 cursor-not-allowed'
                                : 'bg-blue-500 hover:bg-blue-600 text-white'
                        }`}
                    >
                        Update All Data
                    </button>
                </div>
                
                {status?.current_phase && (
                    <div className="text-sm text-gray-600">
                        Current update phase: {status.current_phase}
                    </div>
                )}

                {status?.last_update && (
                    <div className="text-sm text-gray-600">
                        Last successful update: {new Date(status.last_update).toLocaleString()}
                    </div>
                )}
            </div>

            <div className="space-y-6">
                <h2 className="text-xl font-semibold mb-4">Individual Components</h2>
                
                {Object.entries(components).map(([component, details]) => (
                    <div key={component} className="border p-4 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-lg font-medium capitalize">{component}</h3>
                            <button
                                onClick={() => componentUpdateMutation.mutate(component)}
                                disabled={isUpdating}
                                className={`px-3 py-1 rounded-md ${
                                    isUpdating
                                        ? 'bg-gray-300 cursor-not-allowed'
                                        : 'bg-blue-500 hover:bg-blue-600 text-white'
                                }`}
                            >
                                Update {component}
                            </button>
                        </div>
                        
                        <div className="text-sm">
                            <div className="flex items-center gap-2">
                                <span>Status:</span>
                                <span className={`font-medium ${details.updated ? 'text-green-600' : 'text-yellow-600'}`}>
                                    {details.updated ? 'Updated' : 'Not Updated'}
                                </span>
                            </div>
                            
                            {details.last_error && (
                                <div className="mt-2 text-red-600">
                                    Last error: {details.last_error}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
