import React, { useState, useEffect, useRef } from "react";
import { LoadingSpinner } from "../ui/loading-spinner";
import {
  enhanceTableKeyboardNavigation,
  announceToScreenReader,
} from "../../utils/accessibility";
import { useUserPreferences } from "../../utils/userPreferences";

/**
 * Simple table component with basic sorting functionality
 * Replaces the complex DataTable with a clean, user-focused interface
 * Enhanced with mobile responsiveness and accessibility features
 */
export function SimpleTable({
  data = [],
  columns = [],
  loading = false,
  emptyMessage = "No data available",
  onRowClick = null,
  className = "",
  mobileBreakpoint = "md", // Options: sm, md, lg
  tableId = "default", // ID for column visibility preferences
  ...props
}) {
  const { preferences } = useUserPreferences();
  const [sortBy, setSortBy] = useState(null);
  const [sortDirection, setSortDirection] = useState(
    preferences.defaultSortDirection || "asc",
  );
  const tableRef = useRef(null);

  // Filter visible columns based on user preferences
  const visibleColumns = columns.filter(
    (column) => !preferences.hiddenColumns?.[tableId]?.includes(column.key),
  );

  // Use mobile view mode preference
  const shouldShowMobileCards = preferences.mobileViewMode === "cards";

  const handleSort = (columnKey) => {
    const newDirection =
      sortBy === columnKey && sortDirection === "asc" ? "desc" : "asc";
    setSortBy(columnKey);
    setSortDirection(newDirection);

    // Announce sort change to screen readers
    const column = visibleColumns.find((col) => col.key === columnKey);
    if (column && preferences.announceChanges) {
      announceToScreenReader(
        `Table sorted by ${column.header} in ${newDirection}ending order`,
      );
    }
  };

  const handleKeyPress = (event, columnKey) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleSort(columnKey);
    }
  };

  const sortedData = React.useMemo(() => {
    if (!sortBy || !data.length) return data;

    return [...data].sort((a, b) => {
      const aValue = a[sortBy];
      const bValue = b[sortBy];

      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;

      // Handle numbers
      if (typeof aValue === "number" && typeof bValue === "number") {
        return sortDirection === "asc" ? aValue - bValue : bValue - aValue;
      }

      // Handle strings
      const aStr = String(aValue).toLowerCase();
      const bStr = String(bValue).toLowerCase();

      if (sortDirection === "asc") {
        return aStr < bStr ? -1 : aStr > bStr ? 1 : 0;
      } else {
        return aStr > bStr ? -1 : aStr < bStr ? 1 : 0;
      }
    });
  }, [data, sortBy, sortDirection]);

  // Enhanced keyboard navigation
  useEffect(() => {
    if (tableRef.current) {
      const cleanup = enhanceTableKeyboardNavigation(tableRef.current, {
        announceCell: true,
        wrapNavigation: false,
      });
      return cleanup;
    }
  }, [data, sortedData]);

  if (loading) {
    return (
      <div
        className="flex items-center justify-center h-64"
        role="status"
        aria-label="Loading data"
      >
        <LoadingSpinner size="large" />
        <span className="sr-only">Loading...</span>
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="text-center py-12 text-muted-foreground" role="status">
        {emptyMessage}
      </div>
    );
  }

  const SortIcon = ({ column }) => {
    if (sortBy !== column.key) return null;

    return <span className="ml-1">{sortDirection === "asc" ? "↑" : "↓"}</span>;
  };

  return (
    <div className={`overflow-x-auto ${className}`} {...props}>
      {/* Desktop Table View */}
      <table
        ref={tableRef}
        className={`w-full border-collapse hidden ${mobileBreakpoint}:table`}
        role="table"
        aria-label={props["aria-label"] || "Data table"}
        aria-rowcount={sortedData.length + 1}
        aria-colcount={visibleColumns.length}
      >
        <thead>
          <tr className="border-b border-border" role="row">
            {visibleColumns.map((column) => (
              <th
                key={column.key}
                className={`text-left p-4 font-medium text-foreground ${
                  column.sortable !== false
                    ? "cursor-pointer hover:bg-muted/50 focus:bg-muted/50"
                    : ""
                }`}
                onClick={() =>
                  column.sortable !== false && handleSort(column.key)
                }
                onKeyDown={(e) =>
                  column.sortable !== false && handleKeyPress(e, column.key)
                }
                tabIndex={column.sortable !== false ? 0 : -1}
                role="columnheader"
                aria-sort={
                  sortBy === column.key
                    ? sortDirection === "asc"
                      ? "ascending"
                      : "descending"
                    : column.sortable !== false
                      ? "none"
                      : undefined
                }
              >
                <div className="flex items-center">
                  {column.header}
                  {column.sortable !== false && <SortIcon column={column} />}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody role="rowgroup">
          {sortedData.map((row, index) => (
            <tr
              key={row.id || index}
              className={`border-b border-border/50 hover:bg-muted/30 focus:bg-muted/30 transition-colors ${
                onRowClick ? "cursor-pointer" : ""
              }`}
              onClick={() => onRowClick && onRowClick(row)}
              onKeyDown={(e) => {
                if (onRowClick && (e.key === "Enter" || e.key === " ")) {
                  e.preventDefault();
                  onRowClick(row);
                }
              }}
              tabIndex={onRowClick ? 0 : -1}
              role="row"
            >
              {visibleColumns.map((column) => (
                <td key={column.key} className="p-4" role="gridcell">
                  {column.render
                    ? column.render(row[column.key], row)
                    : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Mobile View - Responsive to user preference */}
      <div
        className={`space-y-4 ${shouldShowMobileCards ? `${mobileBreakpoint}:hidden` : "hidden"}`}
      >
        {sortedData.map((row, index) => (
          <div
            key={row.id || index}
            className={`bg-card border border-border rounded-lg p-4 ${
              onRowClick
                ? "cursor-pointer hover:shadow-md transition-shadow"
                : ""
            }`}
            onClick={() => onRowClick && onRowClick(row)}
            onKeyDown={(e) => {
              if (onRowClick && (e.key === "Enter" || e.key === " ")) {
                e.preventDefault();
                onRowClick(row);
              }
            }}
            tabIndex={onRowClick ? 0 : -1}
            role={onRowClick ? "button" : "article"}
            aria-label={
              onRowClick
                ? `View details for ${row.name || row.title || "item"}`
                : undefined
            }
          >
            {visibleColumns.map((column) => (
              <div
                key={column.key}
                className="flex justify-between items-center py-1"
              >
                <span className="font-medium text-muted-foreground text-sm">
                  {column.header}:
                </span>
                <span className="text-foreground">
                  {column.render
                    ? column.render(row[column.key], row)
                    : row[column.key]}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Mobile Table View - When user prefers table over cards */}
      {!shouldShowMobileCards && (
        <div className={`${mobileBreakpoint}:hidden overflow-x-auto`}>
          <table className="w-full border-collapse text-sm" role="table">
            <thead>
              <tr className="border-b border-border">
                {visibleColumns.map((column) => (
                  <th
                    key={column.key}
                    className="text-left p-2 font-medium text-xs"
                  >
                    {column.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedData.map((row, index) => (
                <tr
                  key={row.id || index}
                  className={`border-b border-border/50 hover:bg-muted/30 ${
                    onRowClick ? "cursor-pointer" : ""
                  }`}
                  onClick={() => onRowClick && onRowClick(row)}
                >
                  {visibleColumns.map((column) => (
                    <td key={column.key} className="p-2 text-xs">
                      {column.render
                        ? column.render(row[column.key], row)
                        : row[column.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default SimpleTable;
