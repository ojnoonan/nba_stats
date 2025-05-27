import React, { useState, useEffect } from "react";
import { AlertCircle, Wifi, WifiOff, RefreshCw, Clock } from "lucide-react";

const ApiErrorBoundary = ({ children, onRetry, fallback: CustomFallback }) => {
  const [error, setError] = useState(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const handleRetry = async () => {
    setIsRetrying(true);
    setRetryCount((prev) => prev + 1);

    try {
      if (onRetry) {
        await onRetry();
      }
      setError(null);
    } catch (retryError) {
      setError(retryError);
    } finally {
      setIsRetrying(false);
    }
  };

  const getErrorType = (error) => {
    if (!error) return "unknown";

    if (!isOnline) return "offline";
    if (error.status >= 500) return "server";
    if (error.status === 429) return "rateLimit";
    if (error.status === 404) return "notFound";
    if (error.status >= 400) return "client";
    if (error.name === "AbortError") return "timeout";
    if (error.message?.includes("Failed to fetch")) return "network";

    return "unknown";
  };

  const getErrorMessage = (errorType) => {
    switch (errorType) {
      case "offline":
        return {
          title: "No Internet Connection",
          message: "Please check your internet connection and try again.",
          suggestion: "Make sure you're connected to the internet.",
        };
      case "server":
        return {
          title: "Server Error",
          message:
            "Our servers are experiencing issues. Please try again in a moment.",
          suggestion: "This is usually temporary. Try refreshing the page.",
        };
      case "rateLimit":
        return {
          title: "Too Many Requests",
          message:
            "You're making requests too quickly. Please wait a moment before trying again.",
          suggestion: "Wait a few seconds before making another request.",
        };
      case "notFound":
        return {
          title: "Content Not Found",
          message: "The requested content could not be found.",
          suggestion:
            "The data you're looking for might have been moved or deleted.",
        };
      case "client":
        return {
          title: "Request Error",
          message: "There was a problem with your request.",
          suggestion: "Please check your input and try again.",
        };
      case "timeout":
        return {
          title: "Request Timeout",
          message: "The request took too long to complete.",
          suggestion: "The server might be busy. Try again in a moment.",
        };
      case "network":
        return {
          title: "Network Error",
          message: "Unable to connect to our servers.",
          suggestion: "Check your internet connection or try again later.",
        };
      default:
        return {
          title: "Something went wrong",
          message: "An unexpected error occurred.",
          suggestion:
            "Try refreshing the page or contact support if the problem persists.",
        };
    }
  };

  const errorType = getErrorType(error);
  const { title, message, suggestion } = getErrorMessage(errorType);

  if (error) {
    if (CustomFallback) {
      return (
        <CustomFallback
          error={error}
          errorType={errorType}
          onRetry={handleRetry}
          isRetrying={isRetrying}
          retryCount={retryCount}
          isOnline={isOnline}
        />
      );
    }

    return (
      <div className="flex items-center justify-center p-8">
        <div className="max-w-md w-full bg-white rounded-lg border shadow-sm p-6">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
              {!isOnline ? (
                <WifiOff className="h-6 w-6 text-red-600" />
              ) : (
                <AlertCircle className="h-6 w-6 text-red-600" />
              )}
            </div>

            <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>

            <p className="text-gray-600 mb-2">{message}</p>

            <p className="text-sm text-gray-500 mb-6">{suggestion}</p>

            {!isOnline && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mb-4">
                <div className="flex items-center text-orange-700">
                  <WifiOff size={16} className="mr-2" />
                  <span className="text-sm">You appear to be offline</span>
                </div>
              </div>
            )}

            {retryCount > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                <div className="flex items-center text-blue-700">
                  <Clock size={16} className="mr-2" />
                  <span className="text-sm">Retry attempt {retryCount}</span>
                </div>
              </div>
            )}

            <div className="space-y-3">
              <button
                onClick={handleRetry}
                disabled={isRetrying || (!isOnline && errorType === "offline")}
                className={`w-full inline-flex items-center justify-center px-4 py-2 rounded-md transition-colors ${
                  isRetrying || (!isOnline && errorType === "offline")
                    ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                    : "bg-blue-600 text-white hover:bg-blue-700"
                }`}
              >
                <RefreshCw
                  size={16}
                  className={`mr-2 ${isRetrying ? "animate-spin" : ""}`}
                />
                {isRetrying ? "Retrying..." : "Try Again"}
              </button>

              {errorType === "offline" && (
                <div className="flex items-center justify-center text-sm text-gray-500">
                  <Wifi
                    className={`mr-2 h-4 w-4 ${isOnline ? "text-green-500" : "text-red-500"}`}
                  />
                  {isOnline ? "Connected" : "Disconnected"}
                </div>
              )}
            </div>

            {error.status && (
              <div className="mt-4 text-xs text-gray-400">
                Error {error.status} • {error.message}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return children;
};

export default ApiErrorBoundary;
