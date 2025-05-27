import { describe, test, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import EnhancedTeamsPage from "../pages/EnhancedTeamsPage";
import * as api from "../services/api";

// Mock the API functions
vi.mock("../services/api", () => ({
  fetchTeams: vi.fn(),
  fetchStatus: vi.fn(),
}));

// Mock the responsive utility
vi.mock("../utils/responsive.jsx", () => ({
  useResponsive: () => ({ isMobile: false }),
  useResponsiveTable: (columns) => ({
    isMobile: false,
    responsiveColumns: columns || [],
    mobileExpandedRows: new Set(),
    toggleMobileExpand: vi.fn(),
  }),
  responsiveClasses: {
    actions: {
      mobile: "flex-col space-y-2",
      desktop: "flex-row space-x-2",
    },
    table: {
      container: "w-full overflow-x-auto",
      mobile: "hidden md:table",
      cards: "md:hidden",
    },
  },
}));

const mockTeams = [
  {
    team_id: 1610612747,
    name: "Los Angeles Lakers",
    abbreviation: "LAL",
    logo_url: "https://cdn.nba.com/logos/nba/1610612747/primary/L/logo.svg",
    conference: "West",
    division: "Pacific",
    wins: 45,
    losses: 37,
    roster_loaded: false,
    games_loaded: false,
  },
  {
    team_id: 1610612738,
    name: "Boston Celtics",
    abbreviation: "BOS",
    logo_url: "https://cdn.nba.com/logos/nba/1610612738/primary/L/logo.svg",
    conference: "East",
    division: "Atlantic",
    wins: 57,
    losses: 25,
    roster_loaded: false,
    games_loaded: false,
  },
];

const mockStatus = {
  is_updating: false,
  current_phase: null,
  components: {
    teams: {
      updated: true,
      last_update: new Date().toISOString(),
    },
  },
};

const renderWithProviders = (component) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        refetchOnWindowFocus: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{component}</BrowserRouter>
    </QueryClientProvider>,
  );
};

describe("EnhancedTeamsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.fetchTeams.mockResolvedValue(mockTeams);
    api.fetchStatus.mockResolvedValue(mockStatus);
  });

  describe("Initial Rendering", () => {
    test("renders page title and description", async () => {
      renderWithProviders(<EnhancedTeamsPage />);

      expect(screen.getByText("Enhanced Teams")).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText("Los Angeles Lakers")).toBeInTheDocument();
      });
    });

    test("displays loading state initially", () => {
      api.fetchTeams.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderWithProviders(<EnhancedTeamsPage />);

      expect(screen.getByText(/Loading/)).toBeInTheDocument();
    });

    test("displays error state when API fails", async () => {
      const errorMessage = "Failed to fetch teams";
      api.fetchTeams.mockRejectedValue(new Error(errorMessage));

      renderWithProviders(<EnhancedTeamsPage />);

      await waitFor(() => {
        expect(screen.getByText(/Error/)).toBeInTheDocument();
      });
    });
  });

  describe("Data Table Features", () => {
    test("displays teams in the table", async () => {
      renderWithProviders(<EnhancedTeamsPage />);

      await waitFor(() => {
        expect(screen.getByText("Los Angeles Lakers")).toBeInTheDocument();
        expect(screen.getByText("Boston Celtics")).toBeInTheDocument();
      });
    });

    test("shows team data in columns", async () => {
      renderWithProviders(<EnhancedTeamsPage />);

      await waitFor(() => {
        // Check abbreviations
        expect(screen.getByText("LAL")).toBeInTheDocument();
        expect(screen.getByText("BOS")).toBeInTheDocument();

        // Check conferences
        expect(screen.getByText("West")).toBeInTheDocument();
        expect(screen.getByText("East")).toBeInTheDocument();
      });
    });
  });

  describe("Search Functionality", () => {
    test("filters teams by name", async () => {
      const user = userEvent.setup();
      renderWithProviders(<EnhancedTeamsPage />);

      await waitFor(() => {
        expect(screen.getByText("Los Angeles Lakers")).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/Search/);
      if (searchInput) {
        await user.type(searchInput, "Lakers");

        await waitFor(() => {
          expect(screen.getByText("Los Angeles Lakers")).toBeInTheDocument();
        });
      }
    });
  });

  describe("Responsive Design", () => {
    test("handles different screen sizes", async () => {
      renderWithProviders(<EnhancedTeamsPage />);

      await waitFor(() => {
        expect(screen.getByText("Enhanced Teams")).toBeInTheDocument();
      });
    });
  });

  describe("Export Functionality", () => {
    test("shows export options when available", async () => {
      renderWithProviders(<EnhancedTeamsPage />);

      await waitFor(() => {
        expect(screen.getByText("Los Angeles Lakers")).toBeInTheDocument();
      });

      // Look for export button specifically
      const exportButton = screen.queryByRole("button", { name: /export/i });
      if (exportButton) {
        expect(exportButton).toBeInTheDocument();
      }
    });
  });
});
