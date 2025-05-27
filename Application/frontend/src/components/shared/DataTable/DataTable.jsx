import React, { useState, useEffect } from "react";
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { LoadingSpinner } from "../../ui/loading-spinner";
import { TooltipWrapper } from "../../ui/tooltip";
import TableRow from "./TableRow";
import TableHeader from "./TableHeader";
import TableActions from "./TableActions";
import AdvancedActions, { AdvancedActionsPanel } from "./AdvancedActions";
import { useTableState } from "../../../hooks/useTableState";
import {
  useResponsiveTable,
  MobileCard,
  responsiveClasses,
} from "../../../utils/responsive.jsx";

/**
 * Universal DataTable component with expandable rows, sorting, filtering, and advanced features
 *
 * @param {Object} props
 * @param {Array} props.columns - Column definitions with optional tooltips
 * @param {Array} props.data - Table data
 * @param {boolean} props.sortable - Enable sorting (default: true)
 * @param {boolean} props.expandable - Enable row expansion (default: false)
 * @param {Function} props.onRowClick - Row click handler for expansion
 * @param {Function} props.renderExpanded - Function to render expanded content
 * @param {Function} props.getRowId - Function to get unique row ID
 * @param {string} props.className - Custom CSS classes
 * @param {boolean} props.loading - Loading state
 * @param {string} props.emptyMessage - Message when no data
 * @param {boolean} props.responsive - Enable responsive design (default: true)
 * @param {boolean} props.enableAdvancedFeatures - Enable advanced table features (default: false)
 * @param {boolean} props.enableSearch - Enable search functionality (default: true when advanced)
 * @param {boolean} props.enableFiltering - Enable column filtering (default: true when advanced)
 * @param {boolean} props.enableColumnVisibility - Enable column show/hide (default: true when advanced)
 * @param {boolean} props.enableExport - Enable data export (default: true when advanced)
 * @param {boolean} props.enableMultiSort - Enable multi-column sorting (default: true when advanced)
 * @param {Array} props.searchFields - Fields to search in (default: all string fields)
 * @param {string} props.title - Table title for actions header
 * @param {boolean} props.enableMobileCards - Enable mobile card layout (default: true)
 * @param {string} props.mobileBreakpoint - Breakpoint for mobile layout (default: 'sm')
 */
const DataTable = ({
  columns,
  data = [],
  sortable = true,
  expandable = false,
  onRowClick,
  renderExpanded,
  getRowId = (row, index) => row.id || index,
  className = "",
  loading = false,
  emptyMessage = "No data available",
  responsive = true,
  enableAdvancedFeatures = false,
  enableSearch = true,
  enableFiltering = true,
  enableColumnVisibility = true,
  enableExport = true,
  enableMultiSort = true,
  searchFields = [],
  title = "",
  enableMobileCards = true,
  mobileBreakpoint = "sm",
}) => {
  const [expandedRows, setExpandedRows] = useState(new Set());

  // Responsive table management
  const {
    isMobile,
    responsiveColumns,
    mobileExpandedRows,
    toggleMobileExpand,
  } = useResponsiveTable(columns, {
    enableMobileCards,
    breakpoint: mobileBreakpoint,
  });

  // Advanced table state management
  const tableState = useTableState(data, responsiveColumns, {
    enableMultiSort: enableAdvancedFeatures && enableMultiSort,
    enableFiltering: enableAdvancedFeatures && enableFiltering,
    enableSearch: enableAdvancedFeatures && enableSearch,
    enableColumnVisibility: enableAdvancedFeatures && enableColumnVisibility,
    searchFields,
  });

  // Use table state for sorting when advanced features are enabled
  const sorting = enableAdvancedFeatures ? tableState.sorting : [];
  const setSorting = enableAdvancedFeatures
    ? tableState.updateSorting
    : () => {};

  // Use processed data when advanced features are enabled
  const tableData = enableAdvancedFeatures ? tableState.data : data;
  const displayColumns = enableAdvancedFeatures
    ? tableState.visibleColumns
    : responsiveColumns;

  const table = useReactTable({
    data: tableData,
    columns: displayColumns,
    state: sortable ? { sorting } : {},
    onSortingChange: sortable ? setSorting : undefined,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel:
      sortable && !enableAdvancedFeatures ? getSortedRowModel() : undefined,
    getRowId: (row, index) => getRowId(row, index),
  });

  // Update table state data when props.data changes
  useEffect(() => {
    if (enableAdvancedFeatures) {
      tableState.updateData(data);
    }
  }, [data, enableAdvancedFeatures, tableState]);

  const handleRowClick = (row) => {
    if (!expandable) return;

    const rowId = getRowId(row.original, row.index);
    const newExpandedRows = new Set(expandedRows);

    if (expandedRows.has(rowId)) {
      newExpandedRows.delete(rowId);
    } else {
      newExpandedRows.add(rowId);
    }

    setExpandedRows(newExpandedRows);

    if (onRowClick) {
      onRowClick(row.original, !expandedRows.has(rowId));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner size="large" />
        <span className="ml-2 text-muted-foreground">Loading...</span>
      </div>
    );
  }

  if (!tableData.length) {
    return (
      <div className="flex items-center justify-center p-8 text-muted-foreground">
        {emptyMessage}
      </div>
    );
  }

  return (
    <TooltipWrapper>
      <div
        className={`rounded-lg border bg-card shadow-sm overflow-hidden ${className}`}
      >
        {/* Advanced Actions Header */}
        {enableAdvancedFeatures && (
          <div className="border-b bg-muted/25 p-4">
            <div
              className={`flex gap-4 ${responsiveClasses.actions.mobile} ${responsiveClasses.actions.tablet} ${responsiveClasses.actions.desktop}`}
            >
              {title && (
                <div className="flex-1">
                  <h3 className="text-lg font-semibold">{title}</h3>
                  <p className="text-sm text-muted-foreground">
                    Showing {tableState.filteredRows} of {tableState.totalRows}{" "}
                    records
                    {tableState.isFiltered && " (filtered)"}
                  </p>
                </div>
              )}
              <AdvancedActionsPanel
                tableState={tableState}
                columns={columns}
                enableSearch={enableSearch}
                enableFiltering={enableFiltering}
                enableColumnVisibility={enableColumnVisibility}
                enableExport={enableExport}
                enableMultiSort={enableMultiSort}
              />
            </div>
          </div>
        )}

        {/* Basic Actions (for non-advanced mode) */}
        {!enableAdvancedFeatures && (
          <TableActions
            onRefresh={() => window.location.reload()}
            showRefresh={false}
          />
        )}

        {/* Mobile Card Layout */}
        {isMobile && enableMobileCards ? (
          <div className="divide-y divide-border">
            {table.getRowModel().rows.map((row) => {
              const rowId = getRowId(row.original, row.index);
              const isMobileExpanded = mobileExpandedRows.has(rowId);

              return (
                <div key={row.id} className="p-4">
                  <MobileCard
                    row={row}
                    columns={displayColumns}
                    onExpand={() => toggleMobileExpand(rowId)}
                    isExpanded={isMobileExpanded}
                    getRowId={getRowId}
                  />
                  {expandable && renderExpanded && (
                    <div className="mt-4 pt-4 border-t">
                      <button
                        onClick={() => handleRowClick(row)}
                        className="w-full text-center py-2 text-sm text-primary hover:text-primary/80"
                      >
                        {expandedRows.has(rowId)
                          ? "Hide Details"
                          : "View Details"}
                      </button>
                      {expandedRows.has(rowId) && (
                        <div className="mt-4 animate-in slide-in-from-top-1 duration-200">
                          {renderExpanded(row.original)}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          /* Desktop Table Layout */
          <div className={responsive ? "overflow-x-auto" : ""}>
            <table
              className={`w-full border-collapse ${responsiveClasses.table.mobile} ${responsiveClasses.table.tablet} ${responsiveClasses.table.desktop}`}
            >
              <thead className="bg-muted/50">
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id} className="border-b">
                    {headerGroup.headers.map((header) => (
                      <TableHeader
                        key={header.id}
                        header={header}
                        sortable={sortable}
                        enableAdvancedFeatures={enableAdvancedFeatures}
                        tableState={tableState}
                      />
                    ))}
                    {expandable && (
                      <th className="w-12 p-3 text-right">
                        <span className="sr-only">Expand</span>
                      </th>
                    )}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => {
                  const rowId = getRowId(row.original, row.index);
                  const isExpanded = expandedRows.has(rowId);

                  return (
                    <React.Fragment key={row.id}>
                      <TableRow
                        row={row}
                        expandable={expandable}
                        isExpanded={isExpanded}
                        onRowClick={() => handleRowClick(row)}
                        getRowId={getRowId}
                      />
                      {expandable && isExpanded && renderExpanded && (
                        <tr>
                          <td
                            colSpan={row.getVisibleCells().length + 1}
                            className="p-0 border-b bg-muted/25"
                          >
                            <div className="p-4 animate-in slide-in-from-top-1 duration-200">
                              {renderExpanded(row.original)}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </TooltipWrapper>
  );
};

export default DataTable;
