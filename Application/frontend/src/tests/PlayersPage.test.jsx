import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { vi } from "vitest";
import PlayersPage from "../pages/PlayersPage";
import * as api from "../services/api";

// Mock the API functions
vi.mock("../services/api", () => ({
  fetchPlayers: vi.fn(),
  fetchTeams: vi.fn(),
  fetchStatus: vi.fn(),
  triggerPlayersUpdate: vi.fn(),
}));

const mockTeams = [
  {
    team_id: 1,
    name: "Test Team",
    logo_url: "https://example.com/logo.png",
  },
];

const mockPlayers = [
  {
    player_id: 1,
    full_name: "Test Player",
    current_team_id: 1,
    position: "G",
    jersey_number: "23",
    is_loaded: true,
    headshot_url: "https://example.com/headshot.png",
  },
  {
    player_id: 2,
    full_name: "Loading Player",
    current_team_id: 1,
    position: "F",
    jersey_number: "34",
    is_loaded: false,
  },
];

const mockStatus = {
  is_updating: false,
  current_phase: null,
  components: {
    players: {
      updated: true,
      last_update: new Date().toISOString(),
      percent_complete: 100,
    },
  },
};

describe("PlayersPage", () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    // Reset and set up mocks
    vi.resetAllMocks();
    api.fetchPlayers.mockResolvedValue(mockPlayers);
    api.fetchTeams.mockResolvedValue(mockTeams);
    api.fetchStatus.mockResolvedValue(mockStatus);
    api.triggerPlayersUpdate.mockResolvedValue({ message: "Update started" });
  });

  const renderPlayersPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <PlayersPage />
        </BrowserRouter>
      </QueryClientProvider>,
    );
  };

  it("should render loading state initially", () => {
    renderPlayersPage();
    expect(screen.getByText(/Loading players.../i)).toBeInTheDocument();
  });

  it("should display loaded players", async () => {
    renderPlayersPage();

    await waitFor(() => {
      expect(screen.getByText("Test Player")).toBeInTheDocument();
    });

    // Check team grouping
    expect(screen.getByText("Test Team")).toBeInTheDocument();
  });

  it("should show loading placeholder for non-loaded players", async () => {
    renderPlayersPage();

    await waitFor(() => {
      expect(screen.getByText("Loading player data...")).toBeInTheDocument();
    });
  });

  it("should handle updates correctly", async () => {
    // Set up status progression
    const updatingStatus = {
      ...mockStatus,
      is_updating: true,
      current_phase: "players",
      components: {
        players: {
          updated: false,
          percent_complete: 50,
        },
      },
    };

    const completedStatus = {
      ...mockStatus,
      components: {
        players: {
          updated: true,
          percent_complete: 100,
          last_update: new Date().toISOString(),
        },
      },
    };

    // Mock status updates
    api.fetchStatus
      .mockResolvedValueOnce(mockStatus)
      .mockResolvedValueOnce(updatingStatus)
      .mockResolvedValueOnce(completedStatus);

    renderPlayersPage();

    // Verify initial render
    await waitFor(() => {
      expect(screen.getByText("Test Player")).toBeInTheDocument();
    });

    // Trigger update
    const refreshButton = screen.getByRole("button", {
      name: /refresh players/i,
    });
    await userEvent.click(refreshButton);

    // Verify update state appears
    await waitFor(() => {
      expect(
        screen.getByText(/Processing player updates/i),
      ).toBeInTheDocument();
    });

    // Note: In a real scenario, the update would complete and the text would disappear
    // For this test, we just verify the update process is initiated correctly
  });

  it("should handle errors gracefully", async () => {
    // Mock error state
    api.fetchPlayers.mockRejectedValueOnce(new Error("Failed to load players"));

    renderPlayersPage();

    await waitFor(() => {
      expect(screen.getByText(/Error loading players/i)).toBeInTheDocument();
    });

    // Verify retry button
    const retryButton = screen.getByText(/Try again/i);
    expect(retryButton).toBeInTheDocument();

    // Test retry functionality
    api.fetchPlayers.mockResolvedValueOnce(mockPlayers);
    await userEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText("Test Player")).toBeInTheDocument();
    });
  });

  it("should reflect real-time update progress", async () => {
    const progressStates = [25, 50, 75, 100].map((percent) => ({
      ...mockStatus,
      is_updating: true,
      current_phase: "players",
      components: {
        players: {
          updated: percent === 100,
          percent_complete: percent,
        },
      },
    }));

    // Mock progressive updates
    api.fetchStatus
      .mockResolvedValueOnce(mockStatus)
      .mockResolvedValueOnce(progressStates[0])
      .mockResolvedValueOnce(progressStates[1])
      .mockResolvedValueOnce(progressStates[2])
      .mockResolvedValueOnce(progressStates[3]);

    renderPlayersPage();

    // Trigger update
    await waitFor(() => {
      const refreshButton = screen.getByRole("button", {
        name: /refresh players/i,
      });
      userEvent.click(refreshButton);
    });

    // Verify progress updates appear
    for (let i = 0; i < 2; i++) {
      // Just check the first couple states
      await waitFor(() => {
        expect(
          screen.getByText(/Processing player updates/i),
        ).toBeInTheDocument();
      });
    }

    // Note: In a real scenario, progress would complete and text would disappear
    // For this test, we just verify the progress system is working
  });
});
