import React from "react";
import { AlertTriangle, RefreshCw, Home, Bug } from "lucide-react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      correlationId: null,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Generate correlation ID for error tracking
    const correlationId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    this.setState({
      error,
      errorInfo,
      correlationId,
    });

    // Log error details for debugging
    console.error("Error Boundary caught an error:", {
      error: error.message,
      stack: error.stack,
      errorInfo,
      correlationId,
      component: this.props.name || "Unknown",
      timestamp: new Date().toISOString(),
    });

    // Send error to monitoring service if available
    if (window.errorReporting) {
      window.errorReporting.captureException(error, {
        correlationId,
        component: this.props.name,
        errorInfo,
      });
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      correlationId: null,
    });

    // Call retry callback if provided
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  handleGoHome = () => {
    window.location.href = "/";
  };

  handleReportBug = () => {
    const { error, correlationId } = this.state;
    const reportData = {
      error: error?.message || "Unknown error",
      correlationId,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    };

    // Open email client with pre-filled bug report
    const subject = encodeURIComponent(`Bug Report - ${correlationId}`);
    const body = encodeURIComponent(
      `Error Details:\n${JSON.stringify(reportData, null, 2)}\n\nSteps to reproduce:\n1. \n2. \n3. `,
    );
    window.open(`mailto:support@example.com?subject=${subject}&body=${body}`);
  };

  render() {
    if (this.state.hasError) {
      const { error, correlationId } = this.state;
      const { fallback: CustomFallback, level = "page" } = this.props;

      // Use custom fallback if provided
      if (CustomFallback) {
        return (
          <CustomFallback
            error={error}
            correlationId={correlationId}
            onRetry={this.handleRetry}
            onGoHome={this.handleGoHome}
            onReportBug={this.handleReportBug}
          />
        );
      }

      // Different error displays based on error level
      if (level === "component") {
        return (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 m-2">
            <div className="flex items-center space-x-2 text-red-700 mb-2">
              <AlertTriangle size={16} />
              <h3 className="font-medium">Component Error</h3>
            </div>
            <p className="text-red-600 text-sm mb-3">
              Something went wrong in this component. You can try refreshing or
              continue using other parts of the app.
            </p>
            <div className="flex space-x-2">
              <button
                onClick={this.handleRetry}
                className="inline-flex items-center px-3 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
              >
                <RefreshCw size={12} className="mr-1" />
                Retry
              </button>
            </div>
            {correlationId && (
              <p className="text-xs text-red-500 mt-2">
                Error ID: {correlationId}
              </p>
            )}
          </div>
        );
      }

      // Full page error display
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>

              <h1 className="text-xl font-semibold text-gray-900 mb-2">
                Oops! Something went wrong
              </h1>

              <p className="text-gray-600 mb-6">
                We encountered an unexpected error. Don't worry, our team has
                been notified and we're working on a fix.
              </p>

              {correlationId && (
                <div className="bg-gray-100 rounded p-3 mb-6">
                  <p className="text-xs text-gray-500 mb-1">Error Reference:</p>
                  <code className="text-xs font-mono text-gray-700 break-all">
                    {correlationId}
                  </code>
                </div>
              )}

              <div className="space-y-3">
                <button
                  onClick={this.handleRetry}
                  className="w-full inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  <RefreshCw size={16} className="mr-2" />
                  Try Again
                </button>

                <button
                  onClick={this.handleGoHome}
                  className="w-full inline-flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                >
                  <Home size={16} className="mr-2" />
                  Go to Homepage
                </button>

                <button
                  onClick={this.handleReportBug}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                >
                  <Bug size={16} className="mr-2" />
                  Report This Issue
                </button>
              </div>

              {process.env.NODE_ENV === "development" && error && (
                <details className="mt-6 text-left">
                  <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                    Debug Information
                  </summary>
                  <div className="mt-2 p-3 bg-gray-100 rounded text-xs">
                    <div className="font-mono text-red-600 mb-2">
                      {error.message}
                    </div>
                    <pre className="text-gray-600 overflow-auto max-h-32">
                      {error.stack}
                    </pre>
                  </div>
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
