// User preferences management for NBA Stats app
import React from "react";

const STORAGE_KEY = "nba_stats_preferences";

const DEFAULT_PREFERENCES = {
  // Display preferences
  theme: "auto", // 'light', 'dark', 'auto'
  density: "comfortable", // 'compact', 'comfortable', 'spacious'
  animations: true,

  // Table preferences
  defaultSortDirection: "desc",
  rowsPerPage: 25,
  showPlayerPhotos: true,
  showTeamLogos: true,

  // Accessibility preferences
  reducedMotion: false,
  highContrast: false,
  largeText: false,
  announceChanges: true,

  // Performance preferences
  prefetchData: true,
  backgroundRefresh: true,
  lowDataMode: false,

  // Content preferences
  favoriteTeams: [],
  favoritePlayers: [],
  hiddenColumns: {},

  // Mobile preferences
  mobileViewMode: "cards", // 'cards', 'table'
  enableSwipeGestures: true,

  // Notification preferences
  updateNotifications: true,
  errorNotifications: true,

  // Advanced preferences
  developerMode: false,
  performanceMonitoring: false,
};

class UserPreferences {
  constructor() {
    this.preferences = this.loadPreferences();
    this.listeners = new Set();
  }

  /**
   * Load preferences from localStorage
   */
  loadPreferences() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        return { ...DEFAULT_PREFERENCES, ...parsed };
      }
    } catch (error) {
      console.warn("Error loading user preferences:", error);
    }
    return { ...DEFAULT_PREFERENCES };
  }

  /**
   * Save preferences to localStorage
   */
  savePreferences() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.preferences));
      this.notifyListeners();
    } catch (error) {
      console.warn("Error saving user preferences:", error);
    }
  }

  /**
   * Get a preference value
   */
  get(key, defaultValue = null) {
    return this.preferences[key] ?? defaultValue;
  }

  /**
   * Set a preference value
   */
  set(key, value) {
    this.preferences[key] = value;
    this.savePreferences();
  }

  /**
   * Update multiple preferences at once
   */
  update(updates) {
    this.preferences = { ...this.preferences, ...updates };
    this.savePreferences();
  }

  /**
   * Reset preferences to defaults
   */
  reset() {
    this.preferences = { ...DEFAULT_PREFERENCES };
    this.savePreferences();
  }

  /**
   * Reset specific preference to default
   */
  resetKey(key) {
    if (key in DEFAULT_PREFERENCES) {
      this.preferences[key] = DEFAULT_PREFERENCES[key];
      this.savePreferences();
    }
  }

  /**
   * Add listener for preference changes
   */
  addListener(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Notify all listeners of changes
   */
  notifyListeners() {
    this.listeners.forEach((listener) => {
      try {
        listener(this.preferences);
      } catch (error) {
        console.warn("Error in preference listener:", error);
      }
    });
  }

  /**
   * Get all preferences
   */
  getAll() {
    return { ...this.preferences };
  }

  /**
   * Add a favorite team
   */
  addFavoriteTeam(teamId) {
    const favorites = new Set(this.preferences.favoriteTeams);
    favorites.add(teamId);
    this.set("favoriteTeams", Array.from(favorites));
  }

  /**
   * Remove a favorite team
   */
  removeFavoriteTeam(teamId) {
    const favorites = new Set(this.preferences.favoriteTeams);
    favorites.delete(teamId);
    this.set("favoriteTeams", Array.from(favorites));
  }

  /**
   * Check if team is favorite
   */
  isFavoriteTeam(teamId) {
    return this.preferences.favoriteTeams.includes(teamId);
  }

  /**
   * Add a favorite player
   */
  addFavoritePlayer(playerId) {
    const favorites = new Set(this.preferences.favoritePlayers);
    favorites.add(playerId);
    this.set("favoritePlayers", Array.from(favorites));
  }

  /**
   * Remove a favorite player
   */
  removeFavoritePlayer(playerId) {
    const favorites = new Set(this.preferences.favoritePlayers);
    favorites.delete(playerId);
    this.set("favoritePlayers", Array.from(favorites));
  }

  /**
   * Check if player is favorite
   */
  isFavoritePlayer(playerId) {
    return this.preferences.favoritePlayers.includes(playerId);
  }

  /**
   * Hide/show table column
   */
  setColumnVisibility(tableId, columnKey, visible) {
    const hiddenColumns = { ...this.preferences.hiddenColumns };
    if (!hiddenColumns[tableId]) {
      hiddenColumns[tableId] = [];
    }

    if (visible) {
      hiddenColumns[tableId] = hiddenColumns[tableId].filter(
        (key) => key !== columnKey,
      );
    } else {
      if (!hiddenColumns[tableId].includes(columnKey)) {
        hiddenColumns[tableId].push(columnKey);
      }
    }

    this.set("hiddenColumns", hiddenColumns);
  }

  /**
   * Check if column is hidden
   */
  isColumnHidden(tableId, columnKey) {
    const hiddenColumns = this.preferences.hiddenColumns[tableId] || [];
    return hiddenColumns.includes(columnKey);
  }

  /**
   * Apply accessibility preferences to DOM
   */
  applyAccessibilityPreferences() {
    const root = document.documentElement;

    // High contrast
    if (this.preferences.highContrast) {
      root.classList.add("high-contrast");
    } else {
      root.classList.remove("high-contrast");
    }

    // Large text
    if (this.preferences.largeText) {
      root.classList.add("large-text");
    } else {
      root.classList.remove("large-text");
    }

    // Reduced motion
    if (this.preferences.reducedMotion) {
      root.classList.add("reduce-motion");
    } else {
      root.classList.remove("reduce-motion");
    }

    // Animations
    if (!this.preferences.animations) {
      root.classList.add("no-animations");
    } else {
      root.classList.remove("no-animations");
    }
  }

  /**
   * Apply theme preferences
   */
  applyThemePreferences() {
    const root = document.documentElement;
    const theme = this.preferences.theme;

    if (theme === "auto") {
      // Use system preference
      const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)",
      ).matches;
      root.classList.toggle("dark", prefersDark);
    } else {
      root.classList.toggle("dark", theme === "dark");
    }
  }

  /**
   * Apply density preferences
   */
  applyDensityPreferences() {
    const root = document.documentElement;
    const density = this.preferences.density;

    root.classList.remove(
      "density-compact",
      "density-comfortable",
      "density-spacious",
    );
    root.classList.add(`density-${density}`);
  }

  /**
   * Apply all preferences to DOM
   */
  applyAllPreferences() {
    this.applyAccessibilityPreferences();
    this.applyThemePreferences();
    this.applyDensityPreferences();
  }

  /**
   * Export preferences for backup
   */
  export() {
    return {
      version: "1.0",
      timestamp: new Date().toISOString(),
      preferences: this.getAll(),
    };
  }

  /**
   * Import preferences from backup
   */
  import(exported) {
    try {
      if (exported.version && exported.preferences) {
        this.preferences = { ...DEFAULT_PREFERENCES, ...exported.preferences };
        this.savePreferences();
        this.applyAllPreferences();
        return true;
      }
    } catch (error) {
      console.warn("Error importing preferences:", error);
    }
    return false;
  }

  /**
   * Get preference statistics
   */
  getStats() {
    return {
      customized: Object.keys(this.preferences).filter(
        (key) => this.preferences[key] !== DEFAULT_PREFERENCES[key],
      ).length,
      favoriteTeams: this.preferences.favoriteTeams.length,
      favoritePlayers: this.preferences.favoritePlayers.length,
      hiddenColumnsCount: Object.values(
        this.preferences.hiddenColumns || {},
      ).reduce((total, columns) => total + columns.length, 0),
    };
  }
}

// Create singleton instance
export const userPreferences = new UserPreferences();

// React hook for using preferences
export const useUserPreferences = () => {
  const [preferences, setPreferences] = React.useState(
    userPreferences.getAll(),
  );

  React.useEffect(() => {
    const unsubscribe = userPreferences.addListener(setPreferences);
    return unsubscribe;
  }, []);

  const updatePreference = React.useCallback((key, value) => {
    userPreferences.set(key, value);
  }, []);

  const updateMultiple = React.useCallback((updates) => {
    userPreferences.update(updates);
  }, []);

  return {
    preferences,
    updatePreference,
    updateMultiple,
    reset: userPreferences.reset.bind(userPreferences),
    export: userPreferences.export.bind(userPreferences),
    import: userPreferences.import.bind(userPreferences),
  };
};

export default userPreferences;
