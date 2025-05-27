import React from "react";
import {
  X,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  RefreshCw,
  Bug,
} from "lucide-react";
import { useError } from "../../contexts/ErrorContext";

const ErrorNotification = ({ error, onDismiss, onRetry, className = "" }) => {
  const { ERROR_SEVERITIES } = useError();

  const getIcon = () => {
    switch (error.severity) {
      case ERROR_SEVERITIES.CRITICAL:
        return <AlertTriangle className="h-5 w-5" />;
      case ERROR_SEVERITIES.HIGH:
        return <AlertCircle className="h-5 w-5" />;
      case ERROR_SEVERITIES.MEDIUM:
        return <Info className="h-5 w-5" />;
      case ERROR_SEVERITIES.LOW:
        return <CheckCircle className="h-5 w-5" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  const getStyles = () => {
    switch (error.severity) {
      case ERROR_SEVERITIES.CRITICAL:
        return {
          container: "bg-red-50 border-red-200 text-red-800",
          icon: "text-red-500",
          button: "text-red-600 hover:text-red-800",
          actionButton: "bg-red-100 hover:bg-red-200 text-red-700",
        };
      case ERROR_SEVERITIES.HIGH:
        return {
          container: "bg-orange-50 border-orange-200 text-orange-800",
          icon: "text-orange-500",
          button: "text-orange-600 hover:text-orange-800",
          actionButton: "bg-orange-100 hover:bg-orange-200 text-orange-700",
        };
      case ERROR_SEVERITIES.MEDIUM:
        return {
          container: "bg-blue-50 border-blue-200 text-blue-800",
          icon: "text-blue-500",
          button: "text-blue-600 hover:text-blue-800",
          actionButton: "bg-blue-100 hover:bg-blue-200 text-blue-700",
        };
      case ERROR_SEVERITIES.LOW:
        return {
          container: "bg-gray-50 border-gray-200 text-gray-800",
          icon: "text-gray-500",
          button: "text-gray-600 hover:text-gray-800",
          actionButton: "bg-gray-100 hover:bg-gray-200 text-gray-700",
        };
      default:
        return {
          container: "bg-gray-50 border-gray-200 text-gray-800",
          icon: "text-gray-500",
          button: "text-gray-600 hover:text-gray-800",
          actionButton: "bg-gray-100 hover:bg-gray-200 text-gray-700",
        };
    }
  };

  const styles = getStyles();

  const handleAction = (action) => {
    if (action.handler) {
      action.handler();
    }
    if (action.dismissOnClick) {
      onDismiss();
    }
  };

  return (
    <div
      className={`border rounded-lg p-4 mb-3 ${styles.container} ${className}`}
    >
      <div className="flex items-start">
        <div className={`flex-shrink-0 ${styles.icon}`}>{getIcon()}</div>

        <div className="ml-3 flex-1">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">{error.title}</h3>

            <button
              onClick={onDismiss}
              className={`flex-shrink-0 ml-2 ${styles.button} hover:bg-black hover:bg-opacity-10 rounded p-1 transition-colors`}
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-1 text-sm">{error.message}</div>

          {error.correlationId && (
            <div className="mt-2 text-xs opacity-75 font-mono">
              ID: {error.correlationId}
            </div>
          )}

          {(error.actions?.length > 0 || onRetry) && (
            <div className="mt-3 flex flex-wrap gap-2">
              {onRetry && (
                <button
                  onClick={onRetry}
                  className={`inline-flex items-center px-3 py-1 text-xs rounded ${styles.actionButton} transition-colors`}
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Retry
                </button>
              )}

              {error.actions?.map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleAction(action)}
                  className={`inline-flex items-center px-3 py-1 text-xs rounded ${styles.actionButton} transition-colors`}
                >
                  {action.icon && <action.icon className="h-3 w-3 mr-1" />}
                  {action.label}
                </button>
              ))}

              {error.severity === ERROR_SEVERITIES.CRITICAL && (
                <button
                  onClick={() => {
                    const reportData = {
                      error: error.originalError?.message || error.message,
                      correlationId: error.correlationId,
                      timestamp: error.timestamp,
                      context: error.context,
                    };

                    const subject = encodeURIComponent(
                      `Critical Error Report - ${error.correlationId}`,
                    );
                    const body = encodeURIComponent(
                      `Critical Error Details:\n${JSON.stringify(reportData, null, 2)}`,
                    );
                    window.open(
                      `mailto:support@example.com?subject=${subject}&body=${body}`,
                    );
                  }}
                  className={`inline-flex items-center px-3 py-1 text-xs rounded ${styles.actionButton} transition-colors`}
                >
                  <Bug className="h-3 w-3 mr-1" />
                  Report Bug
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ErrorNotificationContainer = ({
  position = "top-right",
  maxErrors = 5,
}) => {
  const { errors, removeError } = useError();

  const positionClasses = {
    "top-right": "fixed top-4 right-4 z-50",
    "top-left": "fixed top-4 left-4 z-50",
    "bottom-right": "fixed bottom-4 right-4 z-50",
    "bottom-left": "fixed bottom-4 left-4 z-50",
    "top-center": "fixed top-4 left-1/2 transform -translate-x-1/2 z-50",
    "bottom-center": "fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50",
  };

  const visibleErrors = errors.slice(0, maxErrors);

  if (visibleErrors.length === 0) {
    return null;
  }

  return (
    <div className={`${positionClasses[position]} w-full max-w-sm space-y-2`}>
      {visibleErrors.map((error) => (
        <ErrorNotification
          key={error.id}
          error={error}
          onDismiss={() => removeError(error.id)}
          onRetry={error.context?.retryFunction}
        />
      ))}

      {errors.length > maxErrors && (
        <div className="bg-gray-100 border border-gray-200 rounded-lg p-2 text-center text-sm text-gray-600">
          +{errors.length - maxErrors} more errors
        </div>
      )}
    </div>
  );
};

export default ErrorNotificationContainer;
export { ErrorNotification };
