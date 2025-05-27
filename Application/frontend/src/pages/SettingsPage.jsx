import React, { useState } from "react";
import { useUserPreferences } from "../utils/userPreferences";
import { Button } from "../components/ui/button";
import { LoadingSpinner } from "../components/ui/loading-spinner";

// Settings sections components
const ThemeSettings = ({ preferences, updatePreference }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-semibold">Theme & Appearance</h3>

    <div className="space-y-2">
      <label className="block text-sm font-medium">Theme</label>
      <div className="flex space-x-2">
        {["light", "dark", "auto"].map((theme) => (
          <button
            key={theme}
            onClick={() => updatePreference("theme", theme)}
            className={`px-3 py-1 rounded border text-sm capitalize ${
              preferences.theme === theme
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-card hover:bg-muted border-border"
            }`}
          >
            {theme}
          </button>
        ))}
      </div>
    </div>

    <div className="space-y-2">
      <label className="block text-sm font-medium">Density</label>
      <div className="flex space-x-2">
        {["compact", "comfortable", "spacious"].map((density) => (
          <button
            key={density}
            onClick={() => updatePreference("density", density)}
            className={`px-3 py-1 rounded border text-sm capitalize ${
              preferences.density === density
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-card hover:bg-muted border-border"
            }`}
          >
            {density}
          </button>
        ))}
      </div>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="animations"
        checked={preferences.animations}
        onChange={(e) => updatePreference("animations", e.target.checked)}
        className="rounded"
      />
      <label htmlFor="animations" className="text-sm">
        Enable animations
      </label>
    </div>
  </div>
);

const AccessibilitySettings = ({ preferences, updatePreference }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-semibold">Accessibility</h3>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="reducedMotion"
        checked={preferences.reducedMotion}
        onChange={(e) => updatePreference("reducedMotion", e.target.checked)}
        className="rounded"
      />
      <label htmlFor="reducedMotion" className="text-sm">
        Reduce motion
      </label>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="highContrast"
        checked={preferences.highContrast}
        onChange={(e) => updatePreference("highContrast", e.target.checked)}
        className="rounded"
      />
      <label htmlFor="highContrast" className="text-sm">
        High contrast
      </label>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="largeText"
        checked={preferences.largeText}
        onChange={(e) => updatePreference("largeText", e.target.checked)}
        className="rounded"
      />
      <label htmlFor="largeText" className="text-sm">
        Large text
      </label>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="announceChanges"
        checked={preferences.announceChanges}
        onChange={(e) => updatePreference("announceChanges", e.target.checked)}
        className="rounded"
      />
      <label htmlFor="announceChanges" className="text-sm">
        Announce changes to screen readers
      </label>
    </div>
  </div>
);

const TableSettings = ({ preferences, updatePreference }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-semibold">Table & Data Display</h3>

    <div className="space-y-2">
      <label htmlFor="rowsPerPage" className="block text-sm font-medium">
        Rows per page
      </label>
      <select
        id="rowsPerPage"
        value={preferences.rowsPerPage}
        onChange={(e) =>
          updatePreference("rowsPerPage", parseInt(e.target.value))
        }
        className="block w-32 rounded border border-border bg-card px-3 py-1 text-sm"
      >
        <option value={10}>10</option>
        <option value={25}>25</option>
        <option value={50}>50</option>
        <option value={100}>100</option>
      </select>
    </div>

    <div className="space-y-2">
      <label className="block text-sm font-medium">
        Default sort direction
      </label>
      <div className="flex space-x-2">
        {["asc", "desc"].map((direction) => (
          <button
            key={direction}
            onClick={() => updatePreference("defaultSortDirection", direction)}
            className={`px-3 py-1 rounded border text-sm capitalize ${
              preferences.defaultSortDirection === direction
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-card hover:bg-muted border-border"
            }`}
          >
            {direction === "asc" ? "Ascending" : "Descending"}
          </button>
        ))}
      </div>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="showPlayerPhotos"
        checked={preferences.showPlayerPhotos}
        onChange={(e) => updatePreference("showPlayerPhotos", e.target.checked)}
        className="rounded"
      />
      <label htmlFor="showPlayerPhotos" className="text-sm">
        Show player photos
      </label>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="showTeamLogos"
        checked={preferences.showTeamLogos}
        onChange={(e) => updatePreference("showTeamLogos", e.target.checked)}
        className="rounded"
      />
      <label htmlFor="showTeamLogos" className="text-sm">
        Show team logos
      </label>
    </div>
  </div>
);

const PerformanceSettings = ({ preferences, updatePreference }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-semibold">Performance</h3>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="prefetchData"
        checked={preferences.prefetchData}
        onChange={(e) => updatePreference("prefetchData", e.target.checked)}
        className="rounded"
      />
      <label htmlFor="prefetchData" className="text-sm">
        Prefetch data for faster loading
      </label>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="backgroundRefresh"
        checked={preferences.backgroundRefresh}
        onChange={(e) =>
          updatePreference("backgroundRefresh", e.target.checked)
        }
        className="rounded"
      />
      <label htmlFor="backgroundRefresh" className="text-sm">
        Background data refresh
      </label>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="lowDataMode"
        checked={preferences.lowDataMode}
        onChange={(e) => updatePreference("lowDataMode", e.target.checked)}
        className="rounded"
      />
      <label htmlFor="lowDataMode" className="text-sm">
        Low data mode (reduces quality for slower connections)
      </label>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="performanceMonitoring"
        checked={preferences.performanceMonitoring}
        onChange={(e) =>
          updatePreference("performanceMonitoring", e.target.checked)
        }
        className="rounded"
      />
      <label htmlFor="performanceMonitoring" className="text-sm">
        Enable performance monitoring
      </label>
    </div>
  </div>
);

const MobileSettings = ({ preferences, updatePreference }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-semibold">Mobile Experience</h3>

    <div className="space-y-2">
      <label className="block text-sm font-medium">Mobile view mode</label>
      <div className="flex space-x-2">
        {["cards", "table"].map((mode) => (
          <button
            key={mode}
            onClick={() => updatePreference("mobileViewMode", mode)}
            className={`px-3 py-1 rounded border text-sm capitalize ${
              preferences.mobileViewMode === mode
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-card hover:bg-muted border-border"
            }`}
          >
            {mode}
          </button>
        ))}
      </div>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="enableSwipeGestures"
        checked={preferences.enableSwipeGestures}
        onChange={(e) =>
          updatePreference("enableSwipeGestures", e.target.checked)
        }
        className="rounded"
      />
      <label htmlFor="enableSwipeGestures" className="text-sm">
        Enable swipe gestures
      </label>
    </div>
  </div>
);

const NotificationSettings = ({ preferences, updatePreference }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-semibold">Notifications</h3>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="updateNotifications"
        checked={preferences.updateNotifications}
        onChange={(e) =>
          updatePreference("updateNotifications", e.target.checked)
        }
        className="rounded"
      />
      <label htmlFor="updateNotifications" className="text-sm">
        Data update notifications
      </label>
    </div>

    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        id="errorNotifications"
        checked={preferences.errorNotifications}
        onChange={(e) =>
          updatePreference("errorNotifications", e.target.checked)
        }
        className="rounded"
      />
      <label htmlFor="errorNotifications" className="text-sm">
        Error notifications
      </label>
    </div>
  </div>
);

const FavoritesSettings = ({ preferences, updatePreference }) => {
  const favoriteTeamsCount = preferences.favoriteTeams?.length || 0;
  const favoritePlayersCount = preferences.favoritePlayers?.length || 0;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Favorites</h3>

      <div className="space-y-2">
        <div className="text-sm text-muted-foreground">
          You have {favoriteTeamsCount} favorite teams and{" "}
          {favoritePlayersCount} favorite players.
        </div>
        <div className="text-xs text-muted-foreground">
          Add favorites by clicking the heart icons on team and player pages.
        </div>
      </div>
    </div>
  );
};

const DataManagement = ({
  preferences,
  updatePreference,
  export: exportPreferences,
  import: importPreferences,
  reset,
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [importFile, setImportFile] = useState(null);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const exported = exportPreferences();
      const blob = new Blob([JSON.stringify(exported, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `nba-stats-preferences-${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      setIsExporting(false);
    }
  };

  const handleImport = async () => {
    if (!importFile) return;

    setIsImporting(true);
    try {
      const text = await importFile.text();
      const imported = JSON.parse(text);
      const success = importPreferences(imported);
      if (success) {
        alert("Preferences imported successfully!");
        setImportFile(null);
      } else {
        alert("Failed to import preferences. Please check the file format.");
      }
    } catch (error) {
      alert("Failed to import preferences. Invalid file format.");
    } finally {
      setIsImporting(false);
    }
  };

  const handleReset = () => {
    if (
      window.confirm(
        "Are you sure you want to reset all preferences to default values? This cannot be undone.",
      )
    ) {
      setIsResetting(true);
      try {
        reset();
        alert("Preferences reset successfully!");
      } finally {
        setIsResetting(false);
      }
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Data Management</h3>

      <div className="space-y-4">
        <div>
          <Button
            onClick={handleExport}
            disabled={isExporting}
            className="mb-2"
          >
            {isExporting ? (
              <LoadingSpinner size="small" className="mr-2" />
            ) : null}
            Export Preferences
          </Button>
          <div className="text-xs text-muted-foreground">
            Download your current preferences as a backup file.
          </div>
        </div>

        <div>
          <div className="flex space-x-2 mb-2">
            <input
              type="file"
              accept=".json"
              onChange={(e) => setImportFile(e.target.files[0])}
              className="text-sm"
            />
            <Button
              onClick={handleImport}
              disabled={!importFile || isImporting}
            >
              {isImporting ? (
                <LoadingSpinner size="small" className="mr-2" />
              ) : null}
              Import
            </Button>
          </div>
          <div className="text-xs text-muted-foreground">
            Upload a previously exported preferences file.
          </div>
        </div>

        <div>
          <Button
            onClick={handleReset}
            disabled={isResetting}
            variant="destructive"
          >
            {isResetting ? (
              <LoadingSpinner size="small" className="mr-2" />
            ) : null}
            Reset to Defaults
          </Button>
          <div className="text-xs text-muted-foreground">
            Reset all preferences to their default values.
          </div>
        </div>
      </div>
    </div>
  );
};

export default function SettingsPage() {
  const {
    preferences,
    updatePreference,
    updateMultiple,
    reset,
    export: exportPreferences,
    import: importPreferences,
  } = useUserPreferences();

  const sections = [
    { id: "theme", title: "Theme & Appearance", component: ThemeSettings },
    {
      id: "accessibility",
      title: "Accessibility",
      component: AccessibilitySettings,
    },
    { id: "table", title: "Table & Data", component: TableSettings },
    { id: "performance", title: "Performance", component: PerformanceSettings },
    { id: "mobile", title: "Mobile", component: MobileSettings },
    {
      id: "notifications",
      title: "Notifications",
      component: NotificationSettings,
    },
    { id: "favorites", title: "Favorites", component: FavoritesSettings },
    { id: "data", title: "Data Management", component: DataManagement },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground">
          Customize your NBA Stats experience
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {sections.map(({ id, title, component: Component }) => (
          <div key={id} className="bg-card p-6 rounded-lg border">
            <Component
              preferences={preferences}
              updatePreference={updatePreference}
              updateMultiple={updateMultiple}
              reset={reset}
              export={exportPreferences}
              import={importPreferences}
            />
          </div>
        ))}
      </div>

      {/* Preference Statistics */}
      <div className="bg-muted/50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">Preference Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="font-medium">Theme</div>
            <div className="text-muted-foreground capitalize">
              {preferences.theme}
            </div>
          </div>
          <div>
            <div className="font-medium">Density</div>
            <div className="text-muted-foreground capitalize">
              {preferences.density}
            </div>
          </div>
          <div>
            <div className="font-medium">Favorite Teams</div>
            <div className="text-muted-foreground">
              {preferences.favoriteTeams?.length || 0}
            </div>
          </div>
          <div>
            <div className="font-medium">Favorite Players</div>
            <div className="text-muted-foreground">
              {preferences.favoritePlayers?.length || 0}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
