import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { formatInTimeZone } from 'date-fns-tz'
import { fetchGame, fetchGameStats } from '../services/api'
import { LoadingSpinner } from '../components/ui/loading-spinner'

export default function GameDetailsPage() {
  const { id } = useParams()
  const [hideDNP, setHideDNP] = useState(false)
  const [sortColumn, setSortColumn] = useState('points')
  const [sortDirection, setSortDirection] = useState('desc')

  const { data: game, isLoading: loadingGame, error: gameError } = useQuery({
    queryKey: ['game', id],
    queryFn: () => fetchGame(id),
    enabled: !!id,
    retry: 2
  })

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['gameStats', id],
    queryFn: () => fetchGameStats(id),
    enabled: !!id && game?.status === 'Completed',
    retry: 2
  })

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('desc')
    }
  }

  const sortStats = (stats) => {
    if (!stats) return []
    return [...stats].sort((a, b) => {
      const aValue = a[sortColumn]
      const bValue = b[sortColumn]
      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
    })
  }

  const formatDate = (dateStr) => {
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return formatInTimeZone(new Date(dateStr), timeZone, "MMM d, yyyy h:mm a 'GMT'XXX");
  }

  if (loadingGame || (loadingStats && game?.status === 'Completed')) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    )
  }

  if (gameError) {
    return (
      <div className="flex h-96 items-center justify-center flex-col space-y-4">
        <div className="text-destructive">Error loading game: {gameError.message}</div>
        <Link to="/games" className="text-primary hover:underline">&larr; Back to Games</Link>
      </div>
    )
  }

  if (!game) {
    return (
      <div className="flex h-96 items-center justify-center flex-col space-y-4">
        <div className="text-destructive">Game not found</div>
        <Link to="/games" className="text-primary hover:underline">&larr; Back to Games</Link>
      </div>
    )
  }

  const allStats = stats || []
  const filteredStats = hideDNP ? allStats.filter(stat => stat.minutes !== '0:00') : allStats

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center space-x-4 mb-8">
        <Link to="/games" className="text-primary hover:underline">&larr; Back to Games</Link>
      </div>

      {/* Game Header */}
      <div className="mb-8 rounded-lg bg-card p-6 shadow-lg">
        <div className="text-center">
          <div className="mb-2 text-sm text-muted-foreground">
            {formatDate(game.game_date_utc)}
          </div>
          {game.playoff_round && (
            <div className="mb-4 text-lg font-semibold text-primary">
              {game.playoff_round}
            </div>
          )}
          <div className="grid grid-cols-3 items-center gap-4">
            <div className="text-center">
              <img 
                src={game.home_team?.logo_url} 
                alt={game.home_team?.name}
                className="mx-auto h-16 w-16 object-contain"
              />
              <div className="mt-2 text-lg font-semibold">{game.home_team?.name}</div>
              {game.status === 'Completed' && (
                <div className="text-3xl font-bold">{game.home_score}</div>
              )}
            </div>
            <div className="text-xl font-medium text-muted-foreground">
              {game.status === 'Completed' ? 'Final' : game.status}
            </div>
            <div className="text-center">
              <img 
                src={game.away_team?.logo_url} 
                alt={game.away_team?.name}
                className="mx-auto h-16 w-16 object-contain"
              />
              <div className="mt-2 text-lg font-semibold">{game.away_team?.name}</div>
              {game.status === 'Completed' && (
                <div className="text-3xl font-bold">{game.away_score}</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Show message for upcoming games */}
      {game.status === 'Upcoming' && (
        <div className="text-center py-8">
          <p className="text-lg text-muted-foreground">
            This game hasn't started yet. Check back after {formatDate(game.game_date_utc)} for the box score.
          </p>
        </div>
      )}

      {/* Box Score (only for completed games) */}
      {game.status === 'Completed' && (
        <>
          {/* Box Score Controls */}
          <div className="mb-4 flex items-center justify-between">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={hideDNP}
                onChange={(e) => setHideDNP(e.target.checked)}
                className="rounded border-gray-300 text-primary focus:ring-primary"
              />
              <span className="text-sm">Hide DNP Players</span>
            </label>
          </div>

          {/* Box Score Table */}
          <div className="overflow-x-auto rounded-lg border bg-card shadow-sm">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="p-3 text-left font-semibold">Player</th>
                  <th 
                    className="cursor-pointer p-3 text-right font-semibold hover:text-primary"
                    onClick={() => handleSort('minutes')}
                  >
                    MIN
                  </th>
                  <th 
                    className="cursor-pointer p-3 text-right font-semibold hover:text-primary"
                    onClick={() => handleSort('points')}
                  >
                    PTS
                  </th>
                  <th 
                    className="cursor-pointer p-3 text-right font-semibold hover:text-primary"
                    onClick={() => handleSort('rebounds')}
                  >
                    REB
                  </th>
                  <th 
                    className="cursor-pointer p-3 text-right font-semibold hover:text-primary"
                    onClick={() => handleSort('assists')}
                  >
                    AST
                  </th>
                  <th 
                    className="cursor-pointer p-3 text-right font-semibold hover:text-primary"
                    onClick={() => handleSort('steals')}
                  >
                    STL
                  </th>
                  <th 
                    className="cursor-pointer p-3 text-right font-semibold hover:text-primary"
                    onClick={() => handleSort('blocks')}
                  >
                    BLK
                  </th>
                  <th className="p-3 text-right font-semibold">FG</th>
                  <th className="p-3 text-right font-semibold">3P</th>
                  <th className="p-3 text-right font-semibold">FT</th>
                  <th 
                    className="cursor-pointer p-3 text-right font-semibold hover:text-primary"
                    onClick={() => handleSort('plus_minus')}
                  >
                    +/-
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortStats(filteredStats).map((stat) => (
                  <tr key={stat.stat_id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="p-3">{stat.player_name}</td>
                    <td className="p-3 text-right">{stat.minutes}</td>
                    <td className="p-3 text-right">{stat.points}</td>
                    <td className="p-3 text-right">{stat.rebounds}</td>
                    <td className="p-3 text-right">{stat.assists}</td>
                    <td className="p-3 text-right">{stat.steals}</td>
                    <td className="p-3 text-right">{stat.blocks}</td>
                    <td className="p-3 text-right">{stat.fgm}/{stat.fga}</td>
                    <td className="p-3 text-right">{stat.tpm}/{stat.tpa}</td>
                    <td className="p-3 text-right">{stat.ftm}/{stat.fta}</td>
                    <td className={`p-3 text-right ${stat.plus_minus > 0 ? 'text-green-500' : stat.plus_minus < 0 ? 'text-red-500' : ''}`}>
                      {stat.plus_minus > 0 ? '+' : ''}{stat.plus_minus}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}