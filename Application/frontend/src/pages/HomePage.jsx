import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { 
  fetchTeams, 
  fetchPlayers, 
  fetchGames, 
  fetchStatus, 
  triggerTeamsUpdate,
  triggerPlayersUpdate,
  triggerGamesUpdate,
  cancelUpdate 
} from '../services/api'
import { Card } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { LoadingSpinner } from '../components/ui/loading-spinner'

const HomePage = () => {
  const queryClient = useQueryClient()

  const { 
    data: teams,
    refetch: refetchTeams,
    isFetching: isRefetchingTeams 
  } = useQuery({
    queryKey: ['teams'],
    queryFn: fetchTeams,
    suspense: true
  })

  const { 
    data: players,
    refetch: refetchPlayers,
    isFetching: isRefetchingPlayers 
  } = useQuery({
    queryKey: ['players'],
    queryFn: () => fetchPlayers(null, true),
    suspense: true
  })

  const { 
    data: games,
    refetch: refetchGames,
    isFetching: isRefetchingGames 
  } = useQuery({
    queryKey: ['games'],
    queryFn: () => fetchGames(),
    suspense: true
  })

  const {
    data: status,
    refetch: refetchStatus
  } = useQuery({
    queryKey: ['status'],
    queryFn: fetchStatus
  })

  const handleRefreshAll = async () => {
    try {
      await Promise.all([
        triggerTeamsUpdate(),
        triggerPlayersUpdate(),
        triggerGamesUpdate()
      ])
      // Invalidate all queries at once
      await queryClient.invalidateQueries({
        queryKey: [['teams'], ['players'], ['games'], ['status']]
      })
    } catch (error) {
      console.error('Error refreshing data:', error)
    }
  }

  const handleCancelUpdate = async () => {
    try {
      await cancelUpdate()
      queryClient.invalidateQueries({ queryKey: ['status'] })
    } catch (error) {
      console.error('Error canceling update:', error)
    }
  }

  const sections = [
    {
      title: 'Teams',
      count: teams?.length || 0,
      path: '/teams',
      isLoading: status?.is_updating && status.current_phase === 'teams',
      isRefetching: isRefetchingTeams,
      description: 'Browse NBA teams and their standings',
      refreshKey: 'teams'
    },
    {
      title: 'Players',
      count: players?.length || 0,
      path: '/players',
      isLoading: status?.is_updating && status.current_phase === 'players',
      isRefetching: isRefetchingPlayers,
      description: 'Browse player profiles and statistics',
      refreshKey: 'players'
    },
    {
      title: 'Games',
      count: games?.length || 0,
      path: '/games',
      isLoading: status?.is_updating && status.current_phase === 'games',
      isRefetching: isRefetchingGames,
      description: 'View all NBA game results and details',
      refreshKey: 'games'
    },
    {
      title: 'Upcoming Games',
      count: games?.filter(game => game.status === 'Upcoming').length || 0,
      path: '/upcoming-games',
      isLoading: status?.is_updating && status.current_phase === 'games',
      isRefetching: isRefetchingGames,
      description: 'Check upcoming NBA game schedules',
      refreshKey: 'games'
    }
  ]

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">NBA Stats Dashboard</h1>
          <p className="text-gray-500">
            Last updated: {status?.last_update ? format(new Date(status.last_update), 'PPp') : 'Never'}
          </p>
        </div>
        
        {status?.is_updating && (
          <Button onClick={handleCancelUpdate} variant="outline">
            Cancel Update
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {sections.map((section) => (
          <Card key={section.path} className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-2xl font-bold">{section.title}</h2>
                <p className="text-gray-500">{section.description}</p>
              </div>
              <Button
                variant="outline"
                size="icon"
                onClick={() => handleRefreshAll()}
                disabled={status?.is_updating}
              >
                {section.isLoading || section.isRefetching ? (
                  <LoadingSpinner size="small" />
                ) : (
                  "↻"
                )}
              </Button>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-4xl font-bold">{section.count}</span>
              <Link
                to={section.path}
                className="text-blue-500 hover:text-blue-700 transition-colors"
              >
                View All →
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default HomePage