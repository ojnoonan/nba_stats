import { useState, useMemo, useCallback } from "react";

/**
 * Advanced table state management hook
 * Provides comprehensive state management for tables including sorting, filtering, searching, and column visibility
 *
 * @param {Array} initialData - Initial table data
 * @param {Array} columns - Table column definitions
 * @param {Object} options - Configuration options
 * @returns {Object} Table state and methods
 */
export const useTableState = (initialData = [], columns = [], options = {}) => {
  const {
    enableMultiSort = true,
    enableFiltering = true,
    enableSearch = true,
    enableColumnVisibility = true,
    searchFields = [], // Fields to search in, if empty searches all string fields
    caseSensitiveSearch = false,
  } = options;

  // Core state
  const [data, setData] = useState(initialData);
  const [sorting, setSorting] = useState([]);
  const [filters, setFilters] = useState({});
  const [searchTerm, setSearchTerm] = useState("");
  const [hiddenColumns, setHiddenColumns] = useState(new Set());

  // Column visibility state
  const visibleColumns = useMemo(() => {
    return columns.filter(
      (col) => !hiddenColumns.has(col.id || col.accessorKey),
    );
  }, [columns, hiddenColumns]);

  // Search functionality
  const searchData = useCallback(
    (data, term) => {
      if (!term || !enableSearch) return data;

      const searchLower = caseSensitiveSearch ? term : term.toLowerCase();
      const fieldsToSearch =
        searchFields.length > 0
          ? searchFields
          : columns
              .filter(
                (col) => col.accessorKey && typeof col.accessorKey === "string",
              )
              .map((col) => col.accessorKey);

      return data.filter((row) => {
        return fieldsToSearch.some((field) => {
          const value = row[field];
          if (value == null) return false;

          const stringValue = caseSensitiveSearch
            ? String(value)
            : String(value).toLowerCase();

          return stringValue.includes(searchLower);
        });
      });
    },
    [columns, searchFields, caseSensitiveSearch, enableSearch],
  );

  // Filter functionality
  const filterData = useCallback(
    (data, filters) => {
      if (!enableFiltering || Object.keys(filters).length === 0) return data;

      return data.filter((row) => {
        return Object.entries(filters).every(([field, filterConfig]) => {
          const value = row[field];
          const {
            type,
            value: filterValue,
            operator = "equals",
          } = filterConfig;

          if (filterValue == null || filterValue === "") return true;

          switch (type) {
            case "text":
              const searchValue = caseSensitiveSearch
                ? String(value || "")
                : String(value || "").toLowerCase();
              const filterStr = caseSensitiveSearch
                ? String(filterValue)
                : String(filterValue).toLowerCase();

              switch (operator) {
                case "contains":
                  return searchValue.includes(filterStr);
                case "startsWith":
                  return searchValue.startsWith(filterStr);
                case "endsWith":
                  return searchValue.endsWith(filterStr);
                case "equals":
                default:
                  return searchValue === filterStr;
              }

            case "number":
            case "date":
              const numValue =
                type === "date" ? new Date(value).getTime() : Number(value);
              const numFilter =
                type === "date"
                  ? new Date(filterValue).getTime()
                  : Number(filterValue);

              switch (operator) {
                case "gt":
                  return numValue > numFilter;
                case "gte":
                  return numValue >= numFilter;
                case "lt":
                  return numValue < numFilter;
                case "lte":
                  return numValue <= numFilter;
                case "equals":
                default:
                  return numValue === numFilter;
              }

            case "select":
              return Array.isArray(filterValue)
                ? filterValue.includes(value)
                : value === filterValue;

            case "range":
              const { min, max } = filterValue;
              const rangeValue =
                type === "date" ? new Date(value).getTime() : Number(value);
              const minVal =
                min != null
                  ? type === "date"
                    ? new Date(min).getTime()
                    : Number(min)
                  : -Infinity;
              const maxVal =
                max != null
                  ? type === "date"
                    ? new Date(max).getTime()
                    : Number(max)
                  : Infinity;
              return rangeValue >= minVal && rangeValue <= maxVal;

            default:
              return true;
          }
        });
      });
    },
    [enableFiltering, caseSensitiveSearch],
  );

  // Sort functionality
  const sortData = useCallback((data, sortConfig) => {
    if (!sortConfig.length) return data;

    return [...data].sort((a, b) => {
      for (const { id, desc } of sortConfig) {
        const aVal = a[id];
        const bVal = b[id];

        // Handle null/undefined values
        if (aVal == null && bVal == null) continue;
        if (aVal == null) return 1;
        if (bVal == null) return -1;

        // Compare values
        let result = 0;
        if (typeof aVal === "string" && typeof bVal === "string") {
          result = aVal.localeCompare(bVal);
        } else if (typeof aVal === "number" && typeof bVal === "number") {
          result = aVal - bVal;
        } else if (aVal instanceof Date && bVal instanceof Date) {
          result = aVal.getTime() - bVal.getTime();
        } else {
          // Fallback to string comparison
          result = String(aVal).localeCompare(String(bVal));
        }

        if (result !== 0) {
          return desc ? -result : result;
        }
      }
      return 0;
    });
  }, []);

  // Process data through all transformations
  const processedData = useMemo(() => {
    let result = data;
    result = searchData(result, searchTerm);
    result = filterData(result, filters);
    result = sortData(result, sorting);
    return result;
  }, [data, searchTerm, filters, sorting, searchData, filterData, sortData]);

  // Actions
  const updateData = useCallback((newData) => {
    setData(newData);
  }, []);

  const updateSorting = useCallback((newSorting) => {
    setSorting(newSorting);
  }, []);

  const addSort = useCallback(
    (columnId, desc = false) => {
      if (!enableMultiSort) {
        setSorting([{ id: columnId, desc }]);
        return;
      }

      setSorting((prev) => {
        const existing = prev.find((s) => s.id === columnId);
        if (existing) {
          // Update existing sort
          return prev.map((s) => (s.id === columnId ? { ...s, desc } : s));
        } else {
          // Add new sort
          return [...prev, { id: columnId, desc }];
        }
      });
    },
    [enableMultiSort],
  );

  const removeSort = useCallback((columnId) => {
    setSorting((prev) => prev.filter((s) => s.id !== columnId));
  }, []);

  const clearSorting = useCallback(() => {
    setSorting([]);
  }, []);

  const updateFilter = useCallback((field, filterConfig) => {
    setFilters((prev) => ({
      ...prev,
      [field]: filterConfig,
    }));
  }, []);

  const removeFilter = useCallback((field) => {
    setFilters((prev) => {
      const { [field]: removed, ...rest } = prev;
      return rest;
    });
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  const updateSearch = useCallback((term) => {
    setSearchTerm(term);
  }, []);

  const clearSearch = useCallback(() => {
    setSearchTerm("");
  }, []);

  const toggleColumnVisibility = useCallback((columnId) => {
    setHiddenColumns((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(columnId)) {
        newSet.delete(columnId);
      } else {
        newSet.add(columnId);
      }
      return newSet;
    });
  }, []);

  const showColumn = useCallback((columnId) => {
    setHiddenColumns((prev) => {
      const newSet = new Set(prev);
      newSet.delete(columnId);
      return newSet;
    });
  }, []);

  const hideColumn = useCallback((columnId) => {
    setHiddenColumns((prev) => new Set([...prev, columnId]));
  }, []);

  const resetColumnVisibility = useCallback(() => {
    setHiddenColumns(new Set());
  }, []);

  // Export functionality
  const exportData = useCallback(
    (format = "csv", filename = "table-data") => {
      const dataToExport = processedData;
      const visibleColumnIds = visibleColumns.map(
        (col) => col.id || col.accessorKey,
      );

      if (format === "csv") {
        const headers = visibleColumns.map(
          (col) => col.header || col.id || col.accessorKey,
        );
        const csvContent = [
          headers.join(","),
          ...dataToExport.map((row) =>
            visibleColumnIds
              .map((colId) => {
                const value = row[colId];
                // Escape commas and quotes in CSV
                if (
                  typeof value === "string" &&
                  (value.includes(",") || value.includes('"'))
                ) {
                  return `"${value.replace(/"/g, '""')}"`;
                }
                return value || "";
              })
              .join(","),
          ),
        ].join("\n");

        const blob = new Blob([csvContent], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${filename}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === "json") {
        const jsonData = dataToExport.map((row) => {
          const filteredRow = {};
          visibleColumnIds.forEach((colId) => {
            filteredRow[colId] = row[colId];
          });
          return filteredRow;
        });

        const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
          type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${filename}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    },
    [processedData, visibleColumns],
  );

  // Reset all state
  const resetTableState = useCallback(() => {
    setSorting([]);
    setFilters({});
    setSearchTerm("");
    setHiddenColumns(new Set());
  }, []);

  return {
    // Data
    data: processedData,
    originalData: data,

    // State
    sorting,
    filters,
    searchTerm,
    hiddenColumns,
    visibleColumns,

    // Stats
    totalRows: data.length,
    filteredRows: processedData.length,
    isFiltered: Object.keys(filters).length > 0 || searchTerm.length > 0,

    // Actions
    updateData,

    // Sorting
    updateSorting,
    addSort,
    removeSort,
    clearSorting,

    // Filtering
    updateFilter,
    removeFilter,
    clearFilters,

    // Search
    updateSearch,
    clearSearch,

    // Column visibility
    toggleColumnVisibility,
    showColumn,
    hideColumn,
    resetColumnVisibility,

    // Export
    exportData,

    // Reset
    resetTableState,
  };
};

export default useTableState;
