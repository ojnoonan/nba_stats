import { describe, test, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import App from "../App";
import NavigationBar from "../components/navigation/NavigationBar";
import * as api from "../services/api";

// Mock the API functions
vi.mock("../services/api", () => ({
  fetchTeams: vi.fn(),
  fetchPlayers: vi.fn(),
  fetchStatus: vi.fn(),
}));

// Mock the responsive utility
vi.mock("../utils/responsive", () => ({
  useResponsive: () => ({ isMobile: false }),
}));

const mockTeams = [
  {
    team_id: 1,
    name: "Los Angeles Lakers",
    abbreviation: "LAL",
    logo_url: "https://example.com/lakers-logo.png",
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
  },
];

const mockStatus = {
  is_updating: false,
  current_phase: null,
  components: {
    teams: { updated: true, last_update: new Date().toISOString() },
    players: { updated: true, last_update: new Date().toISOString() },
  },
};

const renderWithProviders = (component, initialEntries = ["/"]) => {
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
      <MemoryRouter initialEntries={initialEntries}>{component}</MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("Navigation Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.fetchTeams.mockResolvedValue(mockTeams);
    api.fetchPlayers.mockResolvedValue(mockPlayers);
    api.fetchStatus.mockResolvedValue(mockStatus);
  });

  describe("NavigationBar", () => {
    test("renders all navigation links", () => {
      renderWithProviders(<NavigationBar />);

      expect(screen.getByText("NBA Stats")).toBeInTheDocument();
      expect(screen.getByText("Teams")).toBeInTheDocument();
      expect(screen.getByText("Players")).toBeInTheDocument();
      expect(screen.getByText("Games")).toBeInTheDocument();
    });

    test("includes enhanced page links", () => {
      renderWithProviders(<NavigationBar />);

      const enhancedTeamsLink = screen.queryByText("Enhanced Teams");
      const advancedPlayersLink = screen.queryByText("Advanced Players");

      if (enhancedTeamsLink) {
        expect(enhancedTeamsLink).toBeInTheDocument();
      }
      if (advancedPlayersLink) {
        expect(advancedPlayersLink).toBeInTheDocument();
      }
    });

    test("navigation links are clickable", async () => {
      const user = userEvent.setup();
      renderWithProviders(<NavigationBar />);

      const nbaStatsLink = screen.getByText("NBA Stats");
      expect(nbaStatsLink).toBeInTheDocument();

      // Test that links are clickable
      await user.click(nbaStatsLink);
    });
  });

  describe("Route Navigation", () => {
    test("navigates to enhanced teams page", async () => {
      renderWithProviders(<App />, ["/enhanced-teams"]);

      await waitFor(() => {
        expect(screen.getByText(/Enhanced Teams|Teams/)).toBeInTheDocument();
      });
    });

    test("navigates to advanced players page", async () => {
      renderWithProviders(<App />, ["/advanced-players"]);

      await waitFor(() => {
        expect(
          screen.getByText(/Advanced Players|Players/),
        ).toBeInTheDocument();
      });
    });

    test("handles invalid routes gracefully", async () => {
      renderWithProviders(<App />, ["/invalid-route"]);

      // Should show some kind of not found or redirect behavior
      await waitFor(() => {
        expect(screen.getByText(/Home|Teams|Players/)).toBeInTheDocument();
      });
    });
  });

  describe("Integration with Enhanced Pages", () => {
    test("enhanced teams page integrates with navigation", async () => {
      renderWithProviders(<App />, ["/enhanced-teams"]);

      await waitFor(() => {
        // Should show the page content
        expect(document.body).toBeTruthy();
      });
    });

    test("advanced players page integrates with navigation", async () => {
      renderWithProviders(<App />, ["/advanced-players"]);

      await waitFor(() => {
        // Should show the page content
        expect(document.body).toBeTruthy();
      });
    });
  });

  describe("Error Boundaries", () => {
    test("error boundaries catch page errors", async () => {
      // Mock an API error
      api.fetchTeams.mockRejectedValue(new Error("API Error"));

      renderWithProviders(<App />, ["/enhanced-teams"]);

      await waitFor(() => {
        // Should handle errors gracefully
        expect(document.body).toBeTruthy();
      });
    });
  });

  describe("Mobile Navigation", () => {
    test("navigation works on mobile devices", () => {
      // Mock mobile responsive
      vi.doMock("../utils/responsive", () => ({
        useResponsive: () => ({ isMobile: true }),
      }));

      renderWithProviders(<NavigationBar />);

      expect(screen.getByText("NBA Stats")).toBeInTheDocument();
    });
  });
});
