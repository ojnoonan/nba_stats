import { BrowserRouter } from 'react-router-dom'
import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import HomePage from './pages/HomePage'
import TeamsPage from './pages/TeamsPage'
import PlayersPage from './pages/PlayersPage'
import GamesPage from './pages/GamesPage'
import GameDetailsPage from './pages/GameDetailsPage'
import UpcomingGamesPage from './pages/UpcomingGamesPage'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/teams" element={<TeamsPage />} />
          <Route path="/players" element={<PlayersPage />} />
          <Route path="/players/:id" element={<PlayersPage />} />
          <Route path="/games" element={<GamesPage />} />
          <Route path="/games/:id" element={<GameDetailsPage />} />
          <Route path="/upcoming-games" element={<UpcomingGamesPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
