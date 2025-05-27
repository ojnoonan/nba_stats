import { Suspense, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { LoadingSpinner } from "./components/ui/loading-spinner";
import { Layout } from "./components/layout/Layout";
import { ErrorProvider } from "./contexts/ErrorContext";
import { NavigationProvider } from "./contexts/NavigationContext";
import { ErrorBoundary, ErrorNotificationContainer } from "./components/error";
import HomePage from "./pages/HomePage";
import TeamsPage from "./pages/TeamsPage";
import TeamDetailPage from "./pages/TeamDetailPage";
import PlayersPage from "./pages/PlayersPage";
import GamesPage from "./pages/GamesPage";
import UpcomingGamesPage from "./pages/UpcomingGamesPage";
import GameDetailsPage from "./pages/GameDetailsPage";
import AdminPage from "./pages/AdminPage";
import SettingsPage from "./pages/SettingsPage";
import { userPreferences } from "./utils/userPreferences";
import "./App.css";

const SuspenseFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="large" />
  </div>
);

function App() {
  // Apply user preferences on app startup
  useEffect(() => {
    userPreferences.applyAllPreferences();
  }, []);

  return (
    <ErrorProvider>
      <ErrorBoundary name="App Root">
        <Router>
          <NavigationProvider>
            <Layout>
              <ErrorBoundary name="Layout" level="component">
                <Suspense fallback={<SuspenseFallback />}>
                  <Routes>
                    <Route
                      path="/"
                      element={
                        <ErrorBoundary name="HomePage" level="page">
                          <HomePage />
                        </ErrorBoundary>
                      }
                    />
                    <Route
                      path="/teams"
                      element={
                        <ErrorBoundary name="TeamsPage" level="page">
                          <TeamsPage />
                        </ErrorBoundary>
                      }
                    />
                    <Route
                      path="/teams/:id"
                      element={
                        <ErrorBoundary name="TeamDetailPage" level="page">
                          <TeamDetailPage />
                        </ErrorBoundary>
                      }
                    />
                    <Route
                      path="/players"
                      element={
                        <ErrorBoundary name="PlayersPage" level="page">
                          <PlayersPage />
                        </ErrorBoundary>
                      }
                    />
                    <Route
                      path="/players/:id"
                      element={
                        <ErrorBoundary name="PlayerDetailsPage" level="page">
                          <PlayersPage />
                        </ErrorBoundary>
                      }
                    />
                    <Route
                      path="/games"
                      element={
                        <ErrorBoundary name="GamesPage" level="page">
                          <GamesPage />
                        </ErrorBoundary>
                      }
                    />
                    <Route
                      path="/upcoming-games"
                      element={
                        <ErrorBoundary name="UpcomingGamesPage" level="page">
                          <UpcomingGamesPage />
                        </ErrorBoundary>
                      }
                    />
                    <Route
                      path="/games/:id"
                      element={
                        <ErrorBoundary name="GameDetailsPage" level="page">
                          <GameDetailsPage />
                        </ErrorBoundary>
                      }
                    />
                    <Route
                      path="/admin"
                      element={
                        <ErrorBoundary name="AdminPage" level="page">
                          <AdminPage />
                        </ErrorBoundary>
                      }
                    />
                    <Route
                      path="/settings"
                      element={
                        <ErrorBoundary name="SettingsPage" level="page">
                          <SettingsPage />
                        </ErrorBoundary>
                      }
                    />{" "}
                  </Routes>
                </Suspense>
              </ErrorBoundary>
            </Layout>

            {/* Global Error Notifications */}
            <ErrorNotificationContainer position="top-right" maxErrors={3} />
          </NavigationProvider>
        </Router>
      </ErrorBoundary>
    </ErrorProvider>
  );
}

export default App;
