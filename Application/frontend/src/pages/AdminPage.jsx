import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAdminStatus, triggerFullUpdate, triggerComponentUpdate, cancelAdminUpdate } from '../services/api';
import { Button } from '../components/ui/button';
import { LoadingSpinner } from '../components/ui/loading-spinner';

export default function AdminPage() {
    const queryClient = useQueryClient();
    
    // Helper function to format dates in user's local timezone
    // Backend timestamps are in UTC but don't include timezone info, so we need to explicitly treat them as UTC
    const formatLocalDateTime = (dateString) => {
        if (!dateString) return 'N/A';
        
        // Check if the timestamp already has timezone information
        const hasTimezone = dateString.includes('Z') || 
                           dateString.includes('+') || 
                           (dateString.includes('T') && dateString.includes('-', dateString.indexOf('T')));
        
        // If no timezone info, append 'Z' to treat as UTC
        const utcDateString = hasTimezone ? dateString : dateString + 'Z';
        
        const date = new Date(utcDateString);
        return date.toLocaleString(undefined, {
            hour12: true,
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZoneName: 'short'
        });
    };
    
    const { data: status, isLoading: isLoadingStatus } = useQuery({
        queryKey: ['adminStatus'],
        queryFn: fetchAdminStatus,
        // Refetch more frequently if updating - use a function to access query data safely
        refetchInterval: (data, query) => (data?.is_updating ? 1000 : 5000),
    });

    const fullUpdateMutation = useMutation({
        mutationFn: triggerFullUpdate,
        onSuccess: (data) => {
            queryClient.invalidateQueries(['adminStatus']);
            queryClient.invalidateQueries(['status']); // Also invalidate regular status cache
            console.log('Full update initiated:', data);
        },
        onError: (error) => {
            console.error('Failed to start full update:', error);
        }
    });

    const componentUpdateMutation = useMutation({
        mutationFn: triggerComponentUpdate,
        onSuccess: (data) => {
            queryClient.invalidateQueries(['adminStatus']);
            queryClient.invalidateQueries(['status']); // Also invalidate regular status cache
            console.log('Component update initiated:', data);
        },
        onError: (error) => {
            console.error('Failed to start component update:', error);
        }
    });

    const cancelUpdateMutation = useMutation({
        mutationFn: cancelAdminUpdate,
        onSuccess: (data) => {
            queryClient.invalidateQueries(['adminStatus']);
            queryClient.invalidateQueries(['status']); // Also invalidate regular status cache
            console.log('Update cancelled:', data);
        },
        onError: (error) => {
            console.error('Failed to cancel update:', error);
        }
    });

    if (isLoadingStatus) {
        return <div className="p-4 container mx-auto"><LoadingSpinner /> Loading Admin Dashboard...</div>;
    }

    const isOverallUpdating = status?.is_updating;
    const currentPhase = status?.current_phase;
    const components = status?.components || {};
    const taskInfo = status?.task_info;

    const handleCancel = () => {
        cancelUpdateMutation.mutate();
    };

    return (
        <div className="h-screen flex flex-col">
            <div className=" shadow-sm border-b border-gray-700 p-4">
                <h1 className="text-3xl font-bold text-center text-white">Admin Dashboard</h1>
            </div>
            
            <div className="flex-1 flex overflow-hidden">
                {/* Left Panel - Controls & Management */}
                <div className="w-1/2 border-r border-gray-700  overflow-y-auto">
                    <div className="p-6">
                        <h2 className="text-xl font-bold mb-6 text-gray-100 border-b border-gray-600 pb-2">Data Management</h2>
                        
                        {/* Full Update Section */}
                        <div className="mb-8 p-6 border border-gray-600 rounded-lg shadow-sm bg-gray-700">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-gray-100">Full Update</h3>
                                <div className="flex gap-2">
                                    <Button
                                        onClick={() => fullUpdateMutation.mutate()}
                                        disabled={isOverallUpdating || fullUpdateMutation.isPending}
                                        variant={isOverallUpdating && (currentPhase === 'teams' || currentPhase === 'players' || currentPhase === 'games' || !currentPhase) ? "destructive" : "default"}
                                        className={`px-4 py-2 ${isOverallUpdating && (currentPhase === 'teams' || currentPhase === 'players' || currentPhase === 'games' || !currentPhase) ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-blue-500 hover:bg-blue-600'}`}
                                    >
                                        {(isOverallUpdating && (currentPhase === 'teams' || currentPhase === 'players' || currentPhase === 'games' || !currentPhase)) || fullUpdateMutation.isPending ? <LoadingSpinner size="small" className="mr-2" /> : null}
                                        {isOverallUpdating && (currentPhase === 'teams' || currentPhase === 'players' || currentPhase === 'games' || !currentPhase) ? `Updating ${currentPhase || 'All'}...` : 'Update All Data'}
                                    </Button>
                                    {(isOverallUpdating || cancelUpdateMutation.isPending) && (
                                        <Button
                                            onClick={handleCancel}
                                            disabled={cancelUpdateMutation.isPending}
                                            variant="destructive"
                                            className="bg-red-500 hover:bg-red-600"
                                        >
                                            {cancelUpdateMutation.isPending ? <LoadingSpinner size="small" className="mr-2" /> : null}
                                            {cancelUpdateMutation.isPending ? 'Cancelling...' : 'Cancel Update'}
                                        </Button>
                                    )}
                                </div>
                            </div>
                            
                            {isOverallUpdating && taskInfo && (
                                <div className="mb-4 p-4 bg-blue-900/50 border border-blue-600 rounded-lg">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium text-blue-200">
                                            {taskInfo.name} - {taskInfo.status}
                                        </span>
                                        <span className="text-sm text-blue-300">
                                            {Math.round(taskInfo.progress || 0)}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-600 rounded-full h-2">
                                        <div 
                                            className="bg-blue-500 h-2 rounded-full transition-all duration-300" 
                                            style={{ width: `${taskInfo.progress || 0}%` }}
                                        ></div>
                                    </div>
                                    {taskInfo.message && (
                                        <div className="text-sm text-blue-300 mt-2">
                                            {taskInfo.message}
                                        </div>
                                    )}
                                    {taskInfo.error && (
                                        <div className="text-sm text-red-300 mt-2 bg-red-900/50 p-2 rounded">
                                            Error: {taskInfo.error}
                                        </div>
                                    )}
                                </div>
                            )}
                            
                            {isOverallUpdating && currentPhase && (
                                <div className="text-sm text-gray-300 mb-2">
                                    Current update phase: <span className="font-semibold text-blue-400">{currentPhase}</span>
                                </div>
                            )}

                            {status?.last_update && (
                                <div className="text-sm text-gray-300">
                                    Last successful update: {formatLocalDateTime(status.last_update)}
                                </div>
                            )}
                            {fullUpdateMutation.error && (
                                <div className="mt-2 text-sm text-red-300 bg-red-900/50 p-2 rounded-md">
                                    <strong>Update Error:</strong> {fullUpdateMutation.error.message}
                                </div>
                            )}
                            {cancelUpdateMutation.error && (
                                <div className="mt-2 text-sm text-red-300 bg-red-900/50 p-2 rounded-md">
                                    <strong>Cancel Error:</strong> {cancelUpdateMutation.error.message}
                                </div>
                            )}
                        </div>

                        {/* Individual Components Section */}
                        <div className="space-y-4">
                            <h3 className="text-lg font-semibold text-gray-100 border-b border-gray-600 pb-2">Individual Components</h3>
                            
                            {Object.entries(components).map(([component, details]) => {
                                const isComponentUpdating = isOverallUpdating && currentPhase === component;
                                return (
                                    <div key={component} className="p-4 border border-gray-600 rounded-lg shadow-sm bg-gray-700">
                                        <div className="flex items-center justify-between mb-3">
                                            <h4 className="text-base font-medium capitalize text-gray-200">{component}</h4>
                                            <div className="flex gap-2">
                                                <Button
                                                    onClick={() => componentUpdateMutation.mutate(component)}
                                                    disabled={isOverallUpdating || componentUpdateMutation.isPending}
                                                    variant={isComponentUpdating ? "destructive" : "default"}
                                                    size="sm"
                                                    className={`px-3 py-1 ${isComponentUpdating ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-blue-500 hover:bg-blue-600'}`}
                                                >
                                                    {isComponentUpdating || (componentUpdateMutation.isPending && componentUpdateMutation.variables === component) ? <LoadingSpinner size="small" className="mr-2" /> : null}
                                                    {isComponentUpdating ? `Updating...` : `Update`}
                                                </Button>
                                            </div>
                                        </div>
                                        
                                        <div className="text-sm">
                                            <div className="flex items-center gap-2">
                                                <span className="text-gray-300">Status:</span>
                                                <span className={`font-medium ${details.updated ? 'text-green-400' : 'text-yellow-400'}`}>
                                                    {details.updated ? 'Updated' : (isComponentUpdating ? 'Updating...' : 'Not Updated')}
                                                </span>
                                            </div>
                                        </div>
                                        
                                        {details.last_error && (!isOverallUpdating || currentPhase !== component) && (
                                            <div className="mt-2 text-xs text-red-300 bg-red-900/50 p-2 rounded-md">
                                                Last error: {details.last_error}
                                            </div>
                                        )}
                                        
                                        {componentUpdateMutation.error && componentUpdateMutation.variables === component && (
                                            <div className="mt-2 text-xs text-red-300 bg-red-900/50 p-2 rounded-md">
                                                Update error: {componentUpdateMutation.error.message}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Right Panel - Dashboard & Analytics */}
                <div className="w-1/2 overflow-y-auto">
                    <div className="p-6">
                        <h2 className="text-xl font-bold mb-6 text-gray-100 border-b border-gray-600 pb-2">System Overview</h2>
                        
                        {/* System Status Cards */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
                            <div className=" p-6 rounded-lg shadow-sm border border-gray-700">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-sm font-medium text-gray-300">System Status</h3>
                                        <p className="text-2xl font-bold text-white mt-1">
                                            {isOverallUpdating ? 'Updating' : 'Active'}
                                        </p>
                                    </div>
                                    <div className={`w-3 h-3 rounded-full ${isOverallUpdating ? 'bg-yellow-400' : 'bg-green-400'}`}></div>
                                </div>
                            </div>
                            
                            <div className=" p-6 rounded-lg shadow-sm border border-gray-700">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-sm font-medium text-gray-300">Current Phase</h3>
                                        <p className="text-2xl font-bold text-white mt-1 capitalize">
                                            {currentPhase || 'Idle'}
                                        </p>
                                    </div>
                                    <div className="text-blue-400">
                                        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                        </svg>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Component Status Overview */}
                        <div className=" rounded-lg shadow-sm border border-gray-700 p-6 mb-8">
                            <h3 className="text-lg font-semibold text-gray-100 mb-4">Component Status</h3>
                            <div className="space-y-3">
                                {Object.entries(components).map(([component, details]) => (
                                    <div key={component} className="flex items-center justify-between py-2 px-3 bg-gray-700 rounded-lg">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-2 h-2 rounded-full ${details.updated ? 'bg-green-400' : 'bg-gray-500'}`}></div>
                                            <span className="font-medium text-gray-200 capitalize">{component}</span>
                                        </div>
                                        <span className={`text-sm font-medium ${details.updated ? 'text-green-400' : 'text-gray-400'}`}>
                                            {details.updated ? 'Ready' : 'Pending'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Recent Activity */}
                        <div className=" rounded-lg shadow-sm border border-gray-700 p-6">
                            <h3 className="text-lg font-semibold text-gray-100 mb-4">Recent Activity</h3>
                            <div className="space-y-3">
                                {status?.last_update && (
                                    <div className="flex items-start gap-3 p-3 bg-green-900/30 rounded-lg">
                                        <div className="w-2 h-2 bg-green-400 rounded-full mt-2"></div>
                                        <div>
                                            <p className="text-sm font-medium text-green-300">Last Update Completed</p>
                                            <p className="text-xs text-green-400">{formatLocalDateTime(status.last_update)}</p>
                                        </div>
                                    </div>
                                )}
                                
                                {status?.last_error && (
                                    <div className="flex items-start gap-3 p-3 bg-red-900/30 rounded-lg">
                                        <div className="w-2 h-2 bg-red-400 rounded-full mt-2"></div>
                                        <div>
                                            <p className="text-sm font-medium text-red-300">Last Error</p>
                                            <p className="text-xs text-red-400">{status.last_error}</p>
                                            <p className="text-xs text-red-500">{formatLocalDateTime(status.last_error_time)}</p>
                                        </div>
                                    </div>
                                )}
                                
                                {isOverallUpdating && taskInfo && (
                                    <div className="flex items-start gap-3 p-3 bg-blue-900/30 rounded-lg">
                                        <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 animate-pulse"></div>
                                        <div>
                                            <p className="text-sm font-medium text-blue-300">Current Task</p>
                                            <p className="text-xs text-blue-400">{taskInfo.name} - {taskInfo.status}</p>
                                            {taskInfo.message && (
                                                <p className="text-xs text-blue-500 mt-1">{taskInfo.message}</p>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
