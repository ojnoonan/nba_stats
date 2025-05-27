import { useState, useCallback, useEffect } from "react";
import { useNavigate, useLocation, useSearchParams } from "react-router-dom";

/**
 * Enhanced custom hook for managing table expansion state with URL persistence
 */
export const useTableExpansion = (initialExpanded = [], options = {}) => {
  const {
    persistToUrl = false,
    urlParam = "expanded",
    basePath = "",
    autoExpand = null,
  } = options;

  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();

  // Initialize state from URL if persistence is enabled
  const getInitialExpanded = useCallback(() => {
    if (persistToUrl) {
      const urlExpanded = searchParams.get(urlParam);
      if (urlExpanded) {
        try {
          return new Set(urlExpanded.split(",").filter(Boolean));
        } catch (e) {
          console.warn("Failed to parse expanded state from URL:", e);
        }
      }
    }
    return new Set(initialExpanded);
  }, [persistToUrl, urlParam, searchParams, initialExpanded]);

  const [expandedRows, setExpandedRows] = useState(getInitialExpanded);

  // Update URL when expanded state changes
  useEffect(() => {
    if (persistToUrl && expandedRows.size >= 0) {
      const newSearchParams = new URLSearchParams(searchParams);
      if (expandedRows.size > 0) {
        newSearchParams.set(urlParam, Array.from(expandedRows).join(","));
      } else {
        newSearchParams.delete(urlParam);
      }

      // Only update if params actually changed
      const newParamString = newSearchParams.toString();
      const currentParamString = searchParams.toString();
      if (newParamString !== currentParamString) {
        setSearchParams(newSearchParams, { replace: true });
      }
    }
  }, [expandedRows, persistToUrl, urlParam, searchParams, setSearchParams]);

  // Auto-expand functionality
  useEffect(() => {
    if (autoExpand && typeof autoExpand === "string") {
      expandRow(autoExpand);
    }
  }, [autoExpand]);

  const toggleRow = useCallback((rowId) => {
    setExpandedRows((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(rowId)) {
        newSet.delete(rowId);
      } else {
        newSet.add(rowId);
      }
      return newSet;
    });
  }, []);

  const expandRow = useCallback((rowId) => {
    setExpandedRows((prev) => new Set(prev).add(rowId));
  }, []);

  const collapseRow = useCallback((rowId) => {
    setExpandedRows((prev) => {
      const newSet = new Set(prev);
      newSet.delete(rowId);
      return newSet;
    });
  }, []);

  const isExpanded = useCallback(
    (rowId) => {
      return expandedRows.has(rowId);
    },
    [expandedRows],
  );

  const expandAll = useCallback((rowIds) => {
    setExpandedRows(new Set(rowIds));
  }, []);

  const collapseAll = useCallback(() => {
    setExpandedRows(new Set());
  }, []);

  // Navigation helper for opening in dedicated pages
  const openInPage = useCallback(
    (itemId, itemType) => {
      const paths = {
        team: `/teams/${itemId}`,
        player: `/players/${itemId}`,
        game: `/games/${itemId}`,
      };

      const path = paths[itemType] || `${basePath}/${itemId}`;
      navigate(path);
    },
    [navigate, basePath],
  );

  return {
    expandedRows,
    toggleRow,
    expandRow,
    collapseRow,
    isExpanded,
    expandAll,
    collapseAll,
    openInPage,
  };
};

/**
 * Hook for managing table state with filtering and sorting
 */
export const useTableState = (initialData = [], options = {}) => {
  const {
    sortable = true,
    filterable = true,
    searchable = true,
    defaultSort = null,
    defaultFilter = {},
  } = options;

  const [sortConfig, setSortConfig] = useState(defaultSort);
  const [filters, setFilters] = useState(defaultFilter);
  const [searchTerm, setSearchTerm] = useState("");

  const handleSort = useCallback((column, direction = "auto") => {
    setSortConfig((prev) => {
      if (direction === "auto") {
        // Auto-toggle logic
        if (!prev || prev.column !== column) {
          return { column, direction: "asc" };
        } else if (prev.direction === "asc") {
          return { column, direction: "desc" };
        } else {
          return null; // Clear sort
        }
      } else {
        return { column, direction };
      }
    });
  }, []);

  const handleFilter = useCallback((filterKey, filterValue) => {
    setFilters((prev) => ({
      ...prev,
      [filterKey]: filterValue,
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
    setSearchTerm("");
  }, []);

  const processedData = useCallback(() => {
    let result = [...initialData];

    // Apply search
    if (searchable && searchTerm) {
      result = result.filter((item) =>
        Object.values(item).some((value) =>
          String(value).toLowerCase().includes(searchTerm.toLowerCase()),
        ),
      );
    }

    // Apply filters
    if (filterable && Object.keys(filters).length > 0) {
      result = result.filter((item) => {
        return Object.entries(filters).every(([key, value]) => {
          if (!value || value === "all") return true;
          return item[key] === value;
        });
      });
    }

    // Apply sorting
    if (sortable && sortConfig) {
      result.sort((a, b) => {
        const aVal = a[sortConfig.column];
        const bVal = b[sortConfig.column];

        if (aVal === bVal) return 0;

        const direction = sortConfig.direction === "asc" ? 1 : -1;
        return (aVal > bVal ? 1 : -1) * direction;
      });
    }

    return result;
  }, [
    initialData,
    searchTerm,
    filters,
    sortConfig,
    searchable,
    filterable,
    sortable,
  ]);

  return {
    data: processedData(),
    sortConfig,
    filters,
    searchTerm,
    handleSort,
    handleFilter,
    setSearchTerm,
    clearFilters,
    isFiltered: Object.keys(filters).length > 0 || searchTerm.length > 0,
  };
};
