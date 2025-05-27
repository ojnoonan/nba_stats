import React from "react";

/**
 * Responsive Design System for DataTable
 * Mobile-first approach with progressive enhancement
 */

export const breakpoints = {
  xs: "475px",
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
};

export const responsiveClasses = {
  // Container classes
  container: {
    mobile: "w-full overflow-hidden",
    tablet: "sm:max-w-none",
    desktop: "lg:max-w-full",
  },

  // Table layout classes
  table: {
    mobile: "min-w-full divide-y divide-border",
    tablet: "sm:min-w-0",
    desktop: "lg:table-auto",
  },

  // Header responsiveness
  header: {
    mobile: "px-3 py-2 text-xs",
    tablet: "sm:px-4 sm:py-3 sm:text-sm",
    desktop: "lg:px-6 lg:py-4",
  },

  // Cell responsiveness
  cell: {
    mobile: "px-3 py-2 text-xs",
    tablet: "sm:px-4 sm:py-3 sm:text-sm",
    desktop: "lg:px-6 lg:py-4",
  },

  // Actions responsiveness
  actions: {
    mobile: "flex-col space-y-2",
    tablet: "sm:flex-row sm:space-y-0 sm:space-x-2",
    desktop: "lg:justify-between",
  },

  // Hide columns on mobile
  hideOnMobile: "hidden sm:table-cell",
  hideOnTablet: "hidden md:table-cell",
  hideOnDesktop: "hidden lg:table-cell",

  // Show only on specific sizes
  showOnMobile: "sm:hidden",
  showOnTablet: "hidden sm:block md:hidden",
  showOnDesktop: "hidden lg:block",
};

/**
 * Determines responsive behavior for columns based on priority
 * @param {Array} columns - Table columns
 * @returns {Array} Columns with responsive classes
 */
export const applyResponsiveColumns = (columns) => {
  return columns.map((column) => {
    const priority = column.responsivePriority || "medium";

    let responsiveClasses = "";

    switch (priority) {
      case "high":
        // Always visible
        responsiveClasses = "";
        break;
      case "medium":
        // Hidden on mobile, visible on tablet+
        responsiveClasses = "hidden sm:table-cell";
        break;
      case "low":
        // Hidden on mobile/tablet, visible on desktop+
        responsiveClasses = "hidden md:table-cell";
        break;
      case "lowest":
        // Hidden except on large screens
        responsiveClasses = "hidden lg:table-cell";
        break;
      default:
        responsiveClasses = "";
    }

    return {
      ...column,
      meta: {
        ...column.meta,
        className:
          `${column.meta?.className || ""} ${responsiveClasses}`.trim(),
      },
    };
  });
};

/**
 * Mobile card layout component for table rows
 */
export const MobileCard = ({
  row,
  columns,
  onExpand,
  isExpanded,
  getRowId,
}) => {
  const highPriorityColumns = columns.filter(
    (col) => !col.responsivePriority || col.responsivePriority === "high",
  );

  const otherColumns = columns.filter(
    (col) => col.responsivePriority && col.responsivePriority !== "high",
  );

  return (
    <div className="bg-card border rounded-lg p-4 space-y-3 sm:hidden">
      {/* High priority fields always visible */}
      <div className="space-y-2">
        {highPriorityColumns.map((column) => {
          const cell = row
            .getVisibleCells()
            .find(
              (cell) => cell.column.id === (column.id || column.accessorKey),
            );

          if (!cell) return null;

          return (
            <div
              key={column.id || column.accessorKey}
              className="flex justify-between items-start"
            >
              <span className="text-sm font-medium text-muted-foreground min-w-0 mr-2">
                {typeof column.header === "string" ? column.header : column.id}:
              </span>
              <span className="text-sm text-right flex-1 min-w-0">
                {cell.getValue()}
              </span>
            </div>
          );
        })}
      </div>

      {/* Expandable section for other fields */}
      {otherColumns.length > 0 && (
        <>
          <button
            onClick={() => onExpand?.(row.original)}
            className="w-full text-center py-2 text-sm text-primary hover:text-primary/80 border-t pt-3"
          >
            {isExpanded ? "Show Less" : "Show More"}
          </button>

          {isExpanded && (
            <div className="space-y-2 border-t pt-3 animate-in slide-in-from-top-1 duration-200">
              {otherColumns.map((column) => {
                const cell = row
                  .getVisibleCells()
                  .find(
                    (cell) =>
                      cell.column.id === (column.id || column.accessorKey),
                  );

                if (!cell) return null;

                return (
                  <div
                    key={column.id || column.accessorKey}
                    className="flex justify-between items-start"
                  >
                    <span className="text-sm font-medium text-muted-foreground min-w-0 mr-2">
                      {typeof column.header === "string"
                        ? column.header
                        : column.id}
                      :
                    </span>
                    <span className="text-sm text-right flex-1 min-w-0">
                      {cell.getValue()}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
};

/**
 * Hook for managing responsive table behavior
 */
export const useResponsiveTable = (columns, options = {}) => {
  const { enableMobileCards = true, breakpoint = "sm" } = options;

  const [isMobile, setIsMobile] = React.useState(false);
  const [mobileExpandedRows, setMobileExpandedRows] = React.useState(new Set());

  React.useEffect(() => {
    const checkIsMobile = () => {
      const mediaQuery = window.matchMedia(
        `(max-width: ${breakpoints[breakpoint]})`,
      );
      setIsMobile(mediaQuery.matches);
    };

    checkIsMobile();
    const mediaQuery = window.matchMedia(
      `(max-width: ${breakpoints[breakpoint]})`,
    );
    mediaQuery.addListener(checkIsMobile);

    return () => mediaQuery.removeListener(checkIsMobile);
  }, [breakpoint]);

  const responsiveColumns = React.useMemo(
    () => applyResponsiveColumns(columns),
    [columns],
  );

  const toggleMobileExpand = React.useCallback((rowId) => {
    setMobileExpandedRows((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(rowId)) {
        newSet.delete(rowId);
      } else {
        newSet.add(rowId);
      }
      return newSet;
    });
  }, []);

  return {
    isMobile: isMobile && enableMobileCards,
    responsiveColumns,
    mobileExpandedRows,
    toggleMobileExpand,
  };
};

export default {
  breakpoints,
  responsiveClasses,
  applyResponsiveColumns,
  MobileCard,
  useResponsiveTable,
};
