import React from "react";
import { flexRender } from "@tanstack/react-table";
import { Link } from "react-router-dom";
import {
  ChevronDownIcon,
  ChevronRightIcon,
  ExternalLinkIcon,
} from "lucide-react";

/**
 * Table row component with expansion and navigation capabilities
 */
const TableRow = ({
  row,
  expandable = false,
  isExpanded = false,
  onRowClick,
  getRowId,
  linkTo = null,
  showPageLink = false,
}) => {
  const handleRowClick = (e) => {
    // Don't trigger row expansion if clicking on a link or button
    if (e.target.closest("a, button")) {
      return;
    }

    if (expandable && onRowClick) {
      onRowClick();
    }
  };

  const renderExpandIcon = () => {
    if (!expandable) return null;

    return (
      <button
        onClick={(e) => {
          e.stopPropagation();
          onRowClick?.();
        }}
        className="p-1 rounded hover:bg-muted/50 transition-colors"
        aria-label={isExpanded ? "Collapse row" : "Expand row"}
      >
        {isExpanded ? (
          <ChevronDownIcon className="h-4 w-4" />
        ) : (
          <ChevronRightIcon className="h-4 w-4" />
        )}
      </button>
    );
  };

  const renderPageLink = () => {
    if (!showPageLink || !linkTo) return null;

    return (
      <Link
        to={linkTo}
        className="p-1 rounded hover:bg-muted/50 transition-colors text-muted-foreground hover:text-primary"
        title="Open in dedicated page"
        onClick={(e) => e.stopPropagation()}
      >
        <ExternalLinkIcon className="h-4 w-4" />
      </Link>
    );
  };

  const rowContent = (
    <>
      {row.getVisibleCells().map((cell) => (
        <td key={cell.id} className="p-3 text-sm border-t transition-colors">
          {flexRender(cell.column.columnDef.cell, cell.getContext())}
        </td>
      ))}
      {(expandable || showPageLink) && (
        <td className="p-3 border-t">
          <div className="flex items-center justify-end space-x-1">
            {renderPageLink()}
            {renderExpandIcon()}
          </div>
        </td>
      )}
    </>
  );

  return (
    <tr
      className={`
        hover:bg-muted/50 transition-colors
        ${expandable ? "cursor-pointer" : ""}
        ${isExpanded ? "bg-muted/25" : ""}
      `}
      onClick={handleRowClick}
    >
      {rowContent}
    </tr>
  );
};

export default TableRow;
