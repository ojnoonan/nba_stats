// Accessibility utilities for NBA Stats app

/**
 * Announces content to screen readers
 * @param {string} message - Message to announce
 * @param {string} priority - Priority level: 'polite' | 'assertive'
 */
export const announceToScreenReader = (message, priority = "polite") => {
  const announcement = document.createElement("div");
  announcement.setAttribute("aria-live", priority);
  announcement.setAttribute("aria-atomic", "true");
  announcement.className = "sr-only";
  announcement.textContent = message;

  document.body.appendChild(announcement);

  // Remove the announcement after a short delay
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * Sets focus to an element with fallback handling
 * @param {HTMLElement|string} element - Element or selector to focus
 * @param {object} options - Focus options
 */
export const setFocus = (element, options = {}) => {
  const targetElement =
    typeof element === "string" ? document.querySelector(element) : element;

  if (targetElement && typeof targetElement.focus === "function") {
    // Ensure element is focusable
    if (targetElement.tabIndex === -1) {
      targetElement.tabIndex = 0;
    }

    setTimeout(() => {
      targetElement.focus(options);
    }, 0);
  }
};

/**
 * Manages focus trap for modal dialogs
 * @param {HTMLElement} container - Container element to trap focus within
 * @returns {Function} Cleanup function
 */
export const createFocusTrap = (container) => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  );

  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];

  const handleTabKey = (e) => {
    if (e.key !== "Tab") return;

    if (e.shiftKey) {
      if (document.activeElement === firstFocusable) {
        e.preventDefault();
        lastFocusable.focus();
      }
    } else {
      if (document.activeElement === lastFocusable) {
        e.preventDefault();
        firstFocusable.focus();
      }
    }
  };

  container.addEventListener("keydown", handleTabKey);

  // Focus the first element
  if (firstFocusable) {
    firstFocusable.focus();
  }

  // Return cleanup function
  return () => {
    container.removeEventListener("keydown", handleTabKey);
  };
};

/**
 * Handles keyboard navigation for data tables
 * @param {HTMLTableElement} table - Table element
 * @param {object} options - Navigation options
 */
export const enhanceTableKeyboardNavigation = (table, options = {}) => {
  const { announceCell = true, wrapNavigation = true } = options;

  const cells = table.querySelectorAll("td, th");
  const rows = table.querySelectorAll("tr");

  const getCellPosition = (cell) => {
    const row = cell.closest("tr");
    const rowIndex = Array.from(rows).indexOf(row);
    const cellIndex = Array.from(row.cells).indexOf(cell);
    return { rowIndex, cellIndex };
  };

  const navigateToCell = (rowIndex, cellIndex) => {
    const targetRow = rows[rowIndex];
    if (!targetRow) return;

    const targetCell = targetRow.cells[cellIndex];
    if (!targetCell) return;

    targetCell.focus();

    if (announceCell) {
      const content = targetCell.textContent.trim();
      const columnHeader =
        table.querySelector(`th:nth-child(${cellIndex + 1})`)?.textContent ||
        "";
      announceToScreenReader(`${columnHeader}: ${content}`);
    }
  };

  const handleKeyNavigation = (e) => {
    const currentCell = e.target.closest("td, th");
    if (!currentCell) return;

    const { rowIndex, cellIndex } = getCellPosition(currentCell);

    switch (e.key) {
      case "ArrowRight":
        e.preventDefault();
        const nextCellIndex =
          wrapNavigation &&
          cellIndex === currentCell.parentNode.cells.length - 1
            ? 0
            : cellIndex + 1;
        navigateToCell(rowIndex, nextCellIndex);
        break;

      case "ArrowLeft":
        e.preventDefault();
        const prevCellIndex =
          wrapNavigation && cellIndex === 0
            ? currentCell.parentNode.cells.length - 1
            : cellIndex - 1;
        navigateToCell(rowIndex, prevCellIndex);
        break;

      case "ArrowDown":
        e.preventDefault();
        const nextRowIndex =
          wrapNavigation && rowIndex === rows.length - 1 ? 0 : rowIndex + 1;
        navigateToCell(nextRowIndex, cellIndex);
        break;

      case "ArrowUp":
        e.preventDefault();
        const prevRowIndex =
          wrapNavigation && rowIndex === 0 ? rows.length - 1 : rowIndex - 1;
        navigateToCell(prevRowIndex, cellIndex);
        break;

      case "Home":
        e.preventDefault();
        navigateToCell(rowIndex, 0);
        break;

      case "End":
        e.preventDefault();
        navigateToCell(rowIndex, currentCell.parentNode.cells.length - 1);
        break;
    }
  };

  // Make cells focusable
  cells.forEach((cell) => {
    if (cell.tabIndex === -1) {
      cell.tabIndex = 0;
    }
  });

  table.addEventListener("keydown", handleKeyNavigation);

  return () => {
    table.removeEventListener("keydown", handleKeyNavigation);
  };
};

/**
 * Validates form accessibility
 * @param {HTMLFormElement} form - Form element to validate
 * @returns {object} Validation results
 */
export const validateFormAccessibility = (form) => {
  const issues = [];
  const inputs = form.querySelectorAll("input, select, textarea");

  inputs.forEach((input, index) => {
    // Check for labels
    const hasLabel = input.labels && input.labels.length > 0;
    const hasAriaLabel = input.getAttribute("aria-label");
    const hasAriaLabelledby = input.getAttribute("aria-labelledby");

    if (!hasLabel && !hasAriaLabel && !hasAriaLabelledby) {
      issues.push({
        element: input,
        type: "missing-label",
        message: `Input ${index + 1} is missing a label`,
      });
    }

    // Check for error states
    if (
      input.hasAttribute("aria-invalid") &&
      input.getAttribute("aria-invalid") === "true"
    ) {
      const hasErrorDescription = input.getAttribute("aria-describedby");
      if (!hasErrorDescription) {
        issues.push({
          element: input,
          type: "missing-error-description",
          message: `Input ${index + 1} has error state but no error description`,
        });
      }
    }

    // Check for required fields
    if (input.required && !input.getAttribute("aria-required")) {
      input.setAttribute("aria-required", "true");
    }
  });

  return {
    isValid: issues.length === 0,
    issues,
  };
};

/**
 * Enhances loading states for accessibility
 * @param {HTMLElement} container - Container element
 * @param {boolean} isLoading - Loading state
 * @param {string} loadingMessage - Custom loading message
 */
export const enhanceLoadingState = (
  container,
  isLoading,
  loadingMessage = "Loading...",
) => {
  if (isLoading) {
    container.setAttribute("aria-busy", "true");
    container.setAttribute("aria-live", "polite");
    announceToScreenReader(loadingMessage);
  } else {
    container.removeAttribute("aria-busy");
    container.setAttribute("aria-live", "off");
  }
};

/**
 * Creates skip links for better keyboard navigation
 * @param {Array} links - Array of {href, text} objects
 */
export const createSkipLinks = (links) => {
  const skipContainer = document.createElement("nav");
  skipContainer.className = "skip-links sr-only-focusable";
  skipContainer.setAttribute("aria-label", "Skip navigation");

  const skipList = document.createElement("ul");

  links.forEach((link) => {
    const listItem = document.createElement("li");
    const skipLink = document.createElement("a");

    skipLink.href = link.href;
    skipLink.textContent = link.text;
    skipLink.className = "skip-link";

    // Style for visibility when focused
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 6px;
      background: #000;
      color: #fff;
      padding: 8px;
      z-index: 100;
      text-decoration: none;
      border-radius: 3px;
    `;

    skipLink.addEventListener("focus", () => {
      skipLink.style.top = "6px";
    });

    skipLink.addEventListener("blur", () => {
      skipLink.style.top = "-40px";
    });

    listItem.appendChild(skipLink);
    skipList.appendChild(listItem);
  });

  skipContainer.appendChild(skipList);
  document.body.insertBefore(skipContainer, document.body.firstChild);

  return skipContainer;
};

/**
 * Color contrast checker (basic implementation)
 * @param {string} foreground - Foreground color (hex)
 * @param {string} background - Background color (hex)
 * @returns {object} Contrast information
 */
export const checkColorContrast = (foreground, background) => {
  const hexToRgb = (hex) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16),
        }
      : null;
  };

  const getLuminance = (r, g, b) => {
    const [rs, gs, bs] = [r, g, b].map((c) => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };

  const fgRgb = hexToRgb(foreground);
  const bgRgb = hexToRgb(background);

  if (!fgRgb || !bgRgb) {
    return { error: "Invalid color format" };
  }

  const fgLuminance = getLuminance(fgRgb.r, fgRgb.g, fgRgb.b);
  const bgLuminance = getLuminance(bgRgb.r, bgRgb.g, bgRgb.b);

  const lighter = Math.max(fgLuminance, bgLuminance);
  const darker = Math.min(fgLuminance, bgLuminance);
  const ratio = (lighter + 0.05) / (darker + 0.05);

  return {
    ratio: ratio.toFixed(2),
    passesAA: ratio >= 4.5,
    passesAAA: ratio >= 7,
    passesAALarge: ratio >= 3,
    level:
      ratio >= 7
        ? "AAA"
        : ratio >= 4.5
          ? "AA"
          : ratio >= 3
            ? "AA Large"
            : "Fail",
  };
};
