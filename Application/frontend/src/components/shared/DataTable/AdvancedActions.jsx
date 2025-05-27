import React, { useState } from "react";
import { Button } from "../../ui/button";
import { Dialog } from "../../ui/dialog";

/**
 * Advanced table action components for filtering, sorting, and exporting
 */

// Sort indicator component
export const SortIndicator = ({ column, sortConfig, onSort }) => {
  const isActive = sortConfig?.column === column;
  const direction = isActive ? sortConfig?.direction : null;

  return (
    <button
      onClick={() => onSort(column)}
      className="ml-1 inline-flex flex-col items-center justify-center h-4 w-3 hover:text-primary transition-colors"
      aria-label={`Sort by ${column}`}
    >
      <svg
        className={`h-2 w-2 ${
          isActive && direction === "asc"
            ? "text-primary"
            : "text-muted-foreground/50"
        }`}
        fill="currentColor"
        viewBox="0 0 12 12"
      >
        <path d="M6 0L0 6h12L6 0z" />
      </svg>
      <svg
        className={`h-2 w-2 ${
          isActive && direction === "desc"
            ? "text-primary"
            : "text-muted-foreground/50"
        }`}
        fill="currentColor"
        viewBox="0 0 12 12"
      >
        <path d="M6 12L0 6h12l-6 6z" />
      </svg>
    </button>
  );
};

// Multi-column sort manager
export const MultiSortManager = ({ columns, sortConfig, onMultiSort }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [sortLevels, setSortLevels] = useState([]);

  const addSortLevel = (column, direction) => {
    const newLevel = { column, direction };
    setSortLevels((prev) => [
      ...prev.filter((l) => l.column !== column),
      newLevel,
    ]);
  };

  const removeSortLevel = (column) => {
    setSortLevels((prev) => prev.filter((l) => l.column !== column));
  };

  const applySorts = () => {
    // Convert from our format { column, direction } to useTableState format { id, desc }
    const sortingConfig = sortLevels.map((level) => ({
      id: level.column,
      desc: level.direction === "desc",
    }));
    onMultiSort(sortingConfig);
    setIsOpen(false);
  };

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="text-xs"
      >
        Multi-Sort {sortLevels.length > 0 && `(${sortLevels.length})`}
      </Button>

      <Dialog isOpen={isOpen} onClose={() => setIsOpen(false)}>
        <Dialog.Title>Multi-Column Sorting</Dialog.Title>
        <Dialog.Description>
          Set up multiple sort criteria. Items will be sorted by the first
          criterion, then by subsequent criteria for equal values.
        </Dialog.Description>

        <div className="space-y-4">
          {sortLevels.map((level, index) => (
            <div key={level.column} className="flex items-center space-x-2">
              <span className="text-sm font-medium">{index + 1}.</span>
              <span className="text-sm">{level.column}</span>
              <select
                value={level.direction}
                onChange={(e) => addSortLevel(level.column, e.target.value)}
                className="border rounded px-2 py-1 text-sm"
              >
                <option value="asc">Ascending</option>
                <option value="desc">Descending</option>
              </select>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeSortLevel(level.column)}
                className="text-destructive"
              >
                Remove
              </Button>
            </div>
          ))}

          <div className="border-t pt-4">
            <select
              onChange={(e) => {
                if (e.target.value) {
                  addSortLevel(e.target.value, "asc");
                  e.target.value = "";
                }
              }}
              className="border rounded px-2 py-1 text-sm w-full"
            >
              <option value="">Add sort column...</option>
              {columns
                .filter(
                  (col) =>
                    !sortLevels.find(
                      (l) =>
                        l.column === (col.key || col.id || col.accessorKey),
                    ),
                )
                .map((col) => {
                  const colKey = col.key || col.id || col.accessorKey;
                  const colLabel = col.label || col.header || colKey;
                  return (
                    <option key={colKey} value={colKey}>
                      {colLabel}
                    </option>
                  );
                })}
            </select>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={applySorts}>Apply Sorts</Button>
          </div>
        </div>
      </Dialog>
    </>
  );
};

// Advanced filter component
export const AdvancedFilters = ({
  columns,
  filters,
  onFilterChange,
  onClearFilters,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const filterableColumns = columns.filter((col) => col.filterable);

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="text-xs"
      >
        Filters{" "}
        {Object.keys(filters).length > 0 && `(${Object.keys(filters).length})`}
      </Button>

      <Dialog isOpen={isOpen} onClose={() => setIsOpen(false)}>
        <Dialog.Title>Advanced Filters</Dialog.Title>
        <Dialog.Description>
          Apply filters to narrow down the displayed data.
        </Dialog.Description>

        <div className="space-y-4">
          {filterableColumns.map((column) => {
            const colKey = column.key || column.id || column.accessorKey;
            const colLabel = column.label || column.header || colKey;
            return (
              <div key={colKey} className="space-y-2">
                <label className="text-sm font-medium">{colLabel}</label>
                {column.filterType === "select" ? (
                  <select
                    value={filters[colKey] || ""}
                    onChange={(e) => onFilterChange(colKey, e.target.value)}
                    className="border rounded px-2 py-1 text-sm w-full"
                  >
                    <option value="">All</option>
                    {column.filterOptions?.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                ) : column.filterType === "range" ? (
                  <div className="flex space-x-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={filters[`${colKey}_min`] || ""}
                      onChange={(e) =>
                        onFilterChange(`${colKey}_min`, e.target.value)
                      }
                      className="border rounded px-2 py-1 text-sm flex-1"
                    />
                    <input
                      type="number"
                      placeholder="Max"
                      value={filters[`${colKey}_max`] || ""}
                      onChange={(e) =>
                        onFilterChange(`${colKey}_max`, e.target.value)
                      }
                      className="border rounded px-2 py-1 text-sm flex-1"
                    />
                  </div>
                ) : (
                  <input
                    type="text"
                    placeholder={`Filter by ${colLabel.toLowerCase()}...`}
                    value={filters[colKey] || ""}
                    onChange={(e) => onFilterChange(colKey, e.target.value)}
                    className="border rounded px-2 py-1 text-sm w-full"
                  />
                )}
              </div>
            );
          })}

          <div className="flex justify-between space-x-2 pt-4">
            <Button variant="outline" onClick={onClearFilters}>
              Clear All
            </Button>
            <Button onClick={() => setIsOpen(false)}>Apply Filters</Button>
          </div>
        </div>
      </Dialog>
    </>
  );
};

// Column visibility manager
export const ColumnVisibilityManager = ({
  columns,
  visibleColumns,
  onVisibilityChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="text-xs"
      >
        Columns
      </Button>

      <Dialog isOpen={isOpen} onClose={() => setIsOpen(false)}>
        <Dialog.Title>Manage Columns</Dialog.Title>
        <Dialog.Description>
          Show or hide table columns to customize your view.
        </Dialog.Description>

        <div className="space-y-2">
          {columns.map((column) => {
            const colKey = column.key || column.id || column.accessorKey;
            const colLabel = column.label || column.header || colKey;
            return (
              <div key={colKey} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`col-${colKey}`}
                  checked={visibleColumns.includes(colKey)}
                  onChange={(e) => onVisibilityChange(colKey, e.target.checked)}
                  className="rounded"
                />
                <label htmlFor={`col-${colKey}`} className="text-sm">
                  {colLabel}
                </label>
              </div>
            );
          })}
        </div>

        <div className="flex justify-end pt-4">
          <Button onClick={() => setIsOpen(false)}>Done</Button>
        </div>
      </Dialog>
    </>
  );
};

// Export functionality
export const ExportManager = ({ data, columns, fileName = "data" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedColumns, setSelectedColumns] = useState(
    columns.map((col) => col.key || col.id || col.accessorKey),
  );
  const [format, setFormat] = useState("csv");

  const handleExport = () => {
    const exportData = data.map((row) => {
      const exportRow = {};
      selectedColumns.forEach((colKey) => {
        const column = columns.find(
          (col) => (col.key || col.id || col.accessorKey) === colKey,
        );
        exportRow[column?.label || column?.header || colKey] = row[colKey];
      });
      return exportRow;
    });

    if (format === "csv") {
      exportToCSV(exportData, `${fileName}.csv`);
    } else if (format === "json") {
      exportToJSON(exportData, `${fileName}.json`);
    }

    setIsOpen(false);
  };

  const exportToCSV = (data, filename) => {
    if (data.length === 0) return;

    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(","),
      ...data.map((row) =>
        headers.map((header) => `"${row[header] || ""}"`).join(","),
      ),
    ].join("\n");

    downloadFile(csvContent, filename, "text/csv");
  };

  const exportToJSON = (data, filename) => {
    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile(jsonContent, filename, "application/json");
  };

  const downloadFile = (content, filename, contentType) => {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="text-xs"
      >
        Export
      </Button>

      <Dialog isOpen={isOpen} onClose={() => setIsOpen(false)}>
        <Dialog.Title>Export Data</Dialog.Title>
        <Dialog.Description>
          Export the current data set with your selected columns.
        </Dialog.Description>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="border rounded px-2 py-1 text-sm w-full mt-1"
            >
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
          </div>

          <div>
            <label className="text-sm font-medium">Columns to Export</label>
            <div className="mt-2 space-y-1 max-h-40 overflow-y-auto">
              {columns.map((column) => {
                const colKey = column.key || column.id || column.accessorKey;
                const colLabel = column.label || column.header || colKey;
                return (
                  <div key={colKey} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`export-${colKey}`}
                      checked={selectedColumns.includes(colKey)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedColumns((prev) => [...prev, colKey]);
                        } else {
                          setSelectedColumns((prev) =>
                            prev.filter((col) => col !== colKey),
                          );
                        }
                      }}
                      className="rounded"
                    />
                    <label htmlFor={`export-${colKey}`} className="text-sm">
                      {colLabel}
                    </label>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex justify-between space-x-2 pt-4">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleExport}
              disabled={selectedColumns.length === 0}
            >
              Export ({data.length} rows)
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
};

// Search with highlighting
export const TableSearch = ({
  searchTerm,
  onSearchChange,
  placeholder = "Search...",
}) => {
  return (
    <div className="relative">
      <input
        type="text"
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder={placeholder}
        className="border rounded-md px-3 py-2 pr-8 text-sm w-full focus:outline-none focus:ring-2 focus:ring-primary"
      />
      {searchTerm && (
        <button
          onClick={() => onSearchChange("")}
          className="absolute right-2 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </div>
  );
};

// Combined default export for DataTable integration
const AdvancedActions = {
  SortIndicator,
  MultiSortManager,
  AdvancedFilters,
  ColumnVisibilityManager,
  ExportManager,
  SearchInput: TableSearch, // Alias TableSearch as SearchInput for compatibility
};

// React component wrapper for use in DataTable
export const AdvancedActionsPanel = ({
  tableState,
  columns,
  enableSearch = true,
  enableFiltering = true,
  enableColumnVisibility = true,
  enableExport = true,
  enableMultiSort = true,
}) => {
  return (
    <div className="flex flex-wrap gap-2 items-center">
      {enableSearch && (
        <div className="flex-1 min-w-[200px]">
          <TableSearch
            searchTerm={tableState.searchTerm}
            onSearchChange={tableState.updateSearch}
            placeholder="Search..."
          />
        </div>
      )}

      <div className="flex gap-2 flex-wrap">
        {enableMultiSort && (
          <MultiSortManager
            columns={columns}
            sortConfig={tableState.sorting}
            onMultiSort={tableState.updateSorting}
          />
        )}

        {enableFiltering && (
          <AdvancedFilters
            columns={columns}
            filters={tableState.filters}
            onFilterChange={tableState.updateFilter}
            onClearFilters={tableState.clearFilters}
          />
        )}

        {enableColumnVisibility && (
          <ColumnVisibilityManager
            columns={columns}
            visibleColumns={tableState.visibleColumns.map(
              (col) => col.key || col.id || col.accessorKey,
            )}
            onVisibilityChange={tableState.toggleColumnVisibility}
          />
        )}

        {enableExport && (
          <ExportManager
            data={tableState.data}
            columns={columns}
            fileName="nba_stats_export"
          />
        )}
      </div>
    </div>
  );
};

export default AdvancedActions;
