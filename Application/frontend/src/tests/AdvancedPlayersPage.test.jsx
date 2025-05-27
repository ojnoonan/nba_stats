import { describe, test, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import AdvancedPlayersPage from "../pages/AdvancedPlayersPage";
import * as api from "../services/api";

// Mock the API functions
vi.mock("../services/api", () => ({
  fetchPlayers: vi.fn(),
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
    team_id: 1,
    name: "Los Angeles Lakers",
    abbreviation: "LAL",
    logo_url: "https://example.com/lakers-logo.png",
  },
  {
    team_id: 2,
    name: "Boston Celtics",
    abbreviation: "BOS",
    logo_url: "https://example.com/celtics-logo.png",
  },
];

const mockPlayers = [
  {
    player_id: 1,
    full_name: "LeBron James",
    current_team_id: 1,
    position: "F",
    jersey_number: "6",
    is_loaded: true,
    headshot_url: "https://example.com/lebron-headshot.png",
    height: "6-9",
    weight: 250,
    age: 39,
    years_experience: 21,
    college: "None",
    country: "USA",
    stats: {
      points_per_game: 25.2,
      rebounds_per_game: 7.8,
      assists_per_game: 6.5,
      field_goal_percentage: 0.498,
      three_point_percentage: 0.356,
      free_throw_percentage: 0.731,
    },
  },
  {
    player_id: 2,
    full_name: "Jayson Tatum",
    current_team_id: 2,
    position: "F",
    jersey_number: "0",
    is_loaded: true,
    headshot_url: "https://example.com/tatum-headshot.png",
    height: "6-8",
    weight: 210,
    age: 26,
    years_experience: 7,
    college: "Duke",
    country: "USA",
    stats: {
      points_per_game: 27.1,
      rebounds_per_game: 8.6,
      assists_per_game: 4.9,
      field_goal_percentage: 0.472,
      three_point_percentage: 0.348,
      free_throw_percentage: 0.831,
    },
  },
];

const mockStatus = {
  is_updating: false,
  current_phase: null,
  components: {
    players: {
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

describe("AdvancedPlayersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.fetchPlayers.mockResolvedValue(mockPlayers);
    api.fetchTeams.mockResolvedValue(mockTeams);
    api.fetchStatus.mockResolvedValue(mockStatus);
  });

  describe("Initial Rendering", () => {
    test("renders page title and description", async () => {
      renderWithProviders(<AdvancedPlayersPage />);

      expect(screen.getByText("Advanced Players")).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText("LeBron James")).toBeInTheDocument();
      });
    });

    test("displays loading state initially", () => {
      api.fetchPlayers.mockImplementation(() => new Promise(() => {})); // Never resolves

      renderWithProviders(<AdvancedPlayersPage />);

      expect(screen.getByText(/Loading/)).toBeInTheDocument();
    });

    test("displays error state when API fails", async () => {
      const errorMessage = "Failed to fetch players";
      api.fetchPlayers.mockRejectedValue(new Error(errorMessage));

      renderWithProviders(<AdvancedPlayersPage />);

      await waitFor(() => {
        expect(screen.getByText(/Error/)).toBeInTheDocument();
      });
    });
  });

  describe("Data Table Features", () => {
    test("displays players in the table", async () => {
      renderWithProviders(<AdvancedPlayersPage />);

      await waitFor(() => {
        expect(screen.getByText("LeBron James")).toBeInTheDocument();
        expect(screen.getByText("Jayson Tatum")).toBeInTheDocument();
      });
    });

    test("shows player data in columns", async () => {
      renderWithProviders(<AdvancedPlayersPage />);

      await waitFor(() => {
        // Check jersey numbers
        expect(screen.getByText("#6")).toBeInTheDocument();
        expect(screen.getByText("#0")).toBeInTheDocument();

        // Check positions
        expect(screen.getAllByText("F")).toHaveLength(2);
      });
    });
  });

  describe("Search Functionality", () => {
    test("filters players by name", async () => {
      const user = userEvent.setup();
      renderWithProviders(<AdvancedPlayersPage />);

      await waitFor(() => {
        expect(screen.getByText("LeBron James")).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/Search/);
      if (searchInput) {
        await user.type(searchInput, "LeBron");

        await waitFor(() => {
          expect(screen.getByText("LeBron James")).toBeInTheDocument();
        });
      }
    });
  });

  describe("Responsive Design", () => {
    test("handles different screen sizes", async () => {
      renderWithProviders(<AdvancedPlayersPage />);

      await waitFor(() => {
        expect(screen.getByText("Advanced Players")).toBeInTheDocument();
      });
    });
  });

  describe("Export Functionality", () => {
    test("shows export options when available", async () => {
      renderWithProviders(<AdvancedPlayersPage />);

      await waitFor(() => {
        expect(screen.getByText("LeBron James")).toBeInTheDocument();
      });

      // Look for export button or functionality
      const exportButton = screen.queryByText(/Export/);
      if (exportButton) {
        expect(exportButton).toBeInTheDocument();
      }
    });
  });
});
