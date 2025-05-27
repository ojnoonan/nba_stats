import React from "react";
import { LoadingSpinner } from "../../ui/loading-spinner";

/**
 * Container for expanded row content with loading states and animations
 */
const ExpandedContent = ({
  children,
  loading = false,
  error = null,
  className = "",
}) => {
  if (loading) {
    return (
      <div className={`flex items-center justify-center p-6 ${className}`}>
        <LoadingSpinner size="default" />
        <span className="ml-2 text-muted-foreground">Loading details...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="text-center text-destructive">
          <p>Failed to load details</p>
          <p className="text-sm text-muted-foreground mt-1">{error.message}</p>
        </div>
      </div>
    );
  }

  return <div className={`${className}`}>{children}</div>;
};

export default ExpandedContent;
