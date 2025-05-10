import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { formatInTimeZone } from 'date-fns-tz'
import { fetchGames, fetchTeams, fetchStatus, triggerGamesUpdate } from '../services/api'
import { LoadingSpinner } from '../components/ui/loading-spinner'

const UpcomingGamesPage = () => {
  const queryClient = useQueryClient()

  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: fetchStatus
  })

  const { 
    data: games, 
    isLoading: gamesLoading, 
    error: gamesError,
    refetch: refetchGames,
    isFetching: isRefetching
  } = useQuery({
    queryKey: ['games', 'upcoming'],
    queryFn: () => fetchGames(null, 'Upcoming')
  })

  const { data: teams } = useQuery({
    queryKey: ['teams'],
    queryFn: fetchTeams
  })

  const handleRefresh = async () => {
    try {
      await triggerGamesUpdate()
      await refetchGames()
      await queryClient.invalidateQueries({ queryKey: ['status'] })
    } catch (error) {
      console.error('Error refreshing games:', error)
    }
  }

  const formatGameTime = (dateStr) => {
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return formatInTimeZone(new Date(dateStr), timeZone, "h:mm a 'GMT'XXX");
  }

  if (gamesLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <LoadingSpinner size="large" className="text-primary" />
        <div className="text-muted-foreground">
          {status?.is_updating ? (
            <span>Loading games data...</span>
          ) : (
            <span>Loading...</span>
          )}
        </div>
      </div>
    )
  }

  if (gamesError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <p className="text-destructive">Error loading games: {gamesError.message}</p>
        <button
          onClick={() => refetchGames()}
          className="text-primary hover:underline"
        >
          Try again
        </button>
      </div>
    )
  }

  if (!games?.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <p className="text-muted-foreground text-center">
          The 2024-25 regular season has concluded.<br />
          NBA Playoffs: 8 games remaining
        </p>
        <button
          onClick={() => refetchGames()}
          className="text-primary hover:underline"
        >
          Check for updates
        </button>
      </div>
    )
  }

  const getTeamById = (teamId) => teams?.find(t => t.team_id === teamId)

  const groupGamesByDate = (games) => {
    const grouped = {}
    
    // Group games by date and sort within each day
    games?.forEach(game => {
      const date = format(new Date(game.game_date_utc), 'yyyy-MM-dd')
      if (!grouped[date]) grouped[date] = []
      grouped[date].push(game)
    })
    
    // Sort the dates in ascending order (closest first)
    const sortedDates = Object.keys(grouped).sort((a, b) => {
      return new Date(a) - new Date(b)
    })
    
    const sortedGames = {}
    sortedDates.forEach(date => {
      sortedGames[date] = grouped[date]
    })
    
    return sortedGames
  }

  const groupedGames = groupGamesByDate(games)

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Upcoming Games</h1>
          <p className="text-muted-foreground mt-1">2024-25 NBA Playoffs</p>
        </div>
        <div className="flex items-center space-x-4">
          {status?.is_updating && status.current_phase === 'games' && (
            <div className="flex items-center space-x-2 text-primary">
              <LoadingSpinner size="small" />
              <span>Updating games...</span>
            </div>
          )}
          <button
            onClick={handleRefresh}
            disabled={isRefetching || status?.is_updating}
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
            title="Refresh games"
          >
            <svg
              className={`w-5 h-5 ${isRefetching ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>

      {Object.entries(groupedGames).map(([date, dateGames]) => (
        <div key={date} className="space-y-4">
          <h2 className="text-xl font-semibold">
            {format(new Date(date), 'EEEE, MMMM d, yyyy')}
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dateGames.map((game) => {
              const homeTeam = getTeamById(game.home_team_id)
              const awayTeam = getTeamById(game.away_team_id)

              return (
                <Link
                  key={game.game_id}
                  to={`/games/${game.game_id}`}
                  className="group relative overflow-hidden rounded-lg border bg-card p-6 hover:border-primary transition-colors"
                >
                  {game.playoff_round && (
                    <div className="absolute top-2 right-2 bg-primary text-primary-foreground px-3 py-1 rounded-full text-sm font-medium">
                      {game.playoff_round}
                    </div>
                  )}
                  <div className="flex justify-between items-center">
                    <div className="space-y-4 flex-1">
                      <div className="flex items-center space-x-3">
                        <img
                          src={awayTeam?.logo_url}
                          alt={awayTeam?.name}
                          className="h-8 w-8 object-contain"
                        />
                        <span className="font-semibold">{awayTeam?.name}</span>
                      </div>

                      <div className="flex items-center space-x-3">
                        <img
                          src={homeTeam?.logo_url}
                          alt={homeTeam?.name}
                          className="h-8 w-8 object-contain"
                        />
                        <span className="font-semibold">{homeTeam?.name}</span>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-sm text-muted-foreground">
                        {formatGameTime(game.game_date_utc)}
                      </div>
                      <div className="text-sm font-medium mt-1">
                        {game.status}
                      </div>
                    </div>
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

export default UpcomingGamesPage