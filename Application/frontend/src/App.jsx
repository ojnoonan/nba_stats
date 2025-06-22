import { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { LoadingSpinner } from './components/ui/loading-spinner'
import { Layout } from './components/layout/Layout'
import { SeasonProvider } from './components/SeasonContext'
import HomePage from './pages/HomePage'
import TeamsPage from './pages/TeamsPage'
import PlayersPage from './pages/PlayersPage'
import GamesPage from './pages/GamesPage'
import UpcomingGamesPage from './pages/UpcomingGamesPage'
import GameDetailsPage from './pages/GameDetailsPage'
import AdminPage from './pages/AdminPage'
import './App.css'

const SuspenseFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="large" />
  </div>
)

function App() {
  return (
    <SeasonProvider>
      <Router>
        <Layout>
          <Suspense fallback={<SuspenseFallback />}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/teams" element={<TeamsPage />} />
              <Route path="/players" element={<PlayersPage />} />
              <Route path="/players/:id" element={<PlayersPage />} />
              <Route path="/games" element={<GamesPage />} />
              <Route path="/upcoming-games" element={<UpcomingGamesPage />} />
              <Route path="/games/:id" element={<GameDetailsPage />} />
              <Route path="/admin" element={<AdminPage />} />
            </Routes>
          </Suspense>
        </Layout>
      </Router>
    </SeasonProvider>
  )
}

export default App
