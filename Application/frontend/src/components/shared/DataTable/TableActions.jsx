import React from "react";
import { Link } from "react-router-dom";
import { ExternalLinkIcon, ChevronRightIcon } from "lucide-react";

/**
 * Action buttons for table rows (expand, open in page, etc.)
 */
const TableActions = ({
  expandable = false,
  isExpanded = false,
  onExpand,
  linkTo = null,
  linkLabel = "View details",
}) => {
  const renderExpandButton = () => {
    if (!expandable) return null;

    return (
      <button
        onClick={onExpand}
        className="p-1 rounded hover:bg-muted/50 transition-colors"
        aria-label={isExpanded ? "Collapse" : "Expand"}
        title={isExpanded ? "Collapse" : "Expand"}
      >
        <ChevronRightIcon
          className={`h-4 w-4 transition-transform ${isExpanded ? "rotate-90" : ""}`}
        />
      </button>
    );
  };

  const renderPageLink = () => {
    if (!linkTo) return null;

    return (
      <Link
        to={linkTo}
        className="p-1 rounded hover:bg-muted/50 transition-colors text-muted-foreground hover:text-primary"
        title={linkLabel}
      >
        <ExternalLinkIcon className="h-4 w-4" />
      </Link>
    );
  };

  if (!expandable && !linkTo) {
    return null;
  }

  return (
    <div className="flex items-center justify-end space-x-1">
      {renderPageLink()}
      {renderExpandButton()}
    </div>
  );
};

export default TableActions;
