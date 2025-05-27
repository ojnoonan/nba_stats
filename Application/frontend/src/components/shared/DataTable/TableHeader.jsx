import React from "react";
import { flexRender } from "@tanstack/react-table";
import { Tooltip } from "../../ui/tooltip";
import { SortIndicator } from "./AdvancedActions";

/**
 * Table header component with tooltip support and sorting indicators
 */
const TableHeader = ({
  header,
  sortable = true,
  enableAdvancedFeatures = false,
  tableState = null,
}) => {
  const canSort = sortable && header.column.getCanSort();
  const columnId = header.column.id;

  // Use advanced sorting if enabled
  const sortDirection =
    enableAdvancedFeatures && tableState
      ? (() => {
          const sortConfig = tableState.sorting.find((s) => s.id === columnId);
          return sortConfig ? (sortConfig.desc ? "desc" : "asc") : false;
        })()
      : header.column.getIsSorted();

  const handleSort = (e) => {
    if (!canSort) return;

    if (enableAdvancedFeatures && tableState) {
      // Use advanced multi-sort logic
      if (e.ctrlKey || e.metaKey) {
        // Multi-sort: add/toggle this column in sort stack
        const existingSort = tableState.sorting.find((s) => s.id === columnId);
        if (existingSort) {
          if (existingSort.desc) {
            tableState.removeSort(columnId);
          } else {
            tableState.addSort(columnId, true);
          }
        } else {
          tableState.addSort(columnId, false);
        }
      } else {
        // Single sort: replace all sorting with this column
        if (sortDirection === "asc") {
          tableState.updateSorting([{ id: columnId, desc: true }]);
        } else if (sortDirection === "desc") {
          tableState.updateSorting([]);
        } else {
          tableState.updateSorting([{ id: columnId, desc: false }]);
        }
      }
    } else {
      // Use basic sorting
      header.column.getToggleSortingHandler()?.(e);
    }
  };

  const renderSortIndicator = () => {
    if (!canSort) return null;

    if (enableAdvancedFeatures && tableState) {
      // Show advanced sort indicator with multi-sort support
      const sortIndex = tableState.sorting.findIndex((s) => s.id === columnId);
      return (
        <SortIndicator
          direction={sortDirection}
          sortIndex={sortIndex >= 0 ? sortIndex + 1 : null}
          isMultiSort={tableState.sorting.length > 1}
        />
      );
    }

    // Basic sort indicator
    if (sortDirection === "asc") {
      return <span className="ml-1 text-primary">↑</span>;
    } else if (sortDirection === "desc") {
      return <span className="ml-1 text-primary">↓</span>;
    } else {
      return (
        <span className="ml-1 text-muted-foreground opacity-0 group-hover:opacity-50">
          ↕
        </span>
      );
    }
  };

  const headerContent = flexRender(
    header.column.columnDef.header,
    header.getContext(),
  );

  // Check if header content is wrapped in a Tooltip component
  const isTooltipWrapped =
    React.isValidElement(headerContent) && headerContent.type === Tooltip;

  return (
    <th
      className={`
        p-3 text-left text-sm font-semibold text-foreground
        ${canSort ? "cursor-pointer hover:text-primary group select-none" : ""}
        relative overflow-visible
      `}
      onClick={handleSort}
      title={
        canSort && enableAdvancedFeatures
          ? "Click to sort, Ctrl+Click for multi-sort"
          : undefined
      }
    >
      <div className="flex items-center space-x-1">
        {/* Render header content (may already include tooltip) */}
        {headerContent}
        {renderSortIndicator()}
      </div>
    </th>
  );
};

export default TableHeader;
