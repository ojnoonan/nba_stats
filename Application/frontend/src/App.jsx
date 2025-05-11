import { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { LoadingSpinner } from './components/ui/loading-spinner'
import HomePage from './pages/HomePage'
import TeamsPage from './pages/TeamsPage'
import PlayersPage from './pages/PlayersPage'
import GamesPage from './pages/GamesPage'
import UpcomingGamesPage from './pages/UpcomingGamesPage'
import GameDetailsPage from './pages/GameDetailsPage'
import './App.css'

const SuspenseFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="large" />
  </div>
)

function App() {
  return (
    <Router>
      <div className="container mx-auto px-4 py-8">
        <Suspense fallback={<SuspenseFallback />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/teams" element={<TeamsPage />} />
            <Route path="/players" element={<PlayersPage />} />
            <Route path="/games" element={<GamesPage />} />
            <Route path="/upcoming-games" element={<UpcomingGamesPage />} />
            <Route path="/games/:id" element={<GameDetailsPage />} />
          </Routes>
        </Suspense>
      </div>
    </Router>
  )
}

export default App
