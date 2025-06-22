import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { format } from 'date-fns'
import { formatInTimeZone } from 'date-fns-tz'
import { fetchTeams, fetchStatus, fetchTeam, fetchPlayers, fetchGames, triggerTeamsUpdate } from '../services/api'
import { LoadingSpinner } from '../components/ui/loading-spinner'
import { useState, useEffect, useCallback, useRef } from 'react'
import { useSeason } from '../components/SeasonContext'

const formatGameTime = (dateStr) => {
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return formatInTimeZone(new Date(dateStr), timeZone, "h:mm a 'GMT'XXX");
}

const TeamsPage = () => {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const [expandedTeamId, setExpandedTeamId] = useState(null)
  const { selectedSeason } = useSeason()
  const expandedContentRef = useRef(null)

  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: fetchStatus
  })

  const { 
    data: teams, 
    isLoading: teamsLoading, 
    error: teamsError,
    refetch: refetchTeams,
    isFetching: isRefetching
  } = useQuery({
    queryKey: ['teams'],
    queryFn: fetchTeams
  })

  // Get initial expanded team from URL
  useEffect(() => {
    const expandParam = searchParams.get('expand')
    if (expandParam) {
      const teamId = parseInt(expandParam, 10)
      if (!isNaN(teamId)) {
        setExpandedTeamId(teamId)
      }
    }
  }, [searchParams])

  // Auto-scroll to expanded content when team is expanded from URL
  useEffect(() => {
    if (expandedTeamId && expandedContentRef.current && teams) {
      // Small delay to ensure the content is rendered
      const timeoutId = setTimeout(() => {
        expandedContentRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        })
      }, 100)
      
      return () => clearTimeout(timeoutId)
    }
  }, [expandedTeamId, teams])

  // Update URL when expanded team changes
  const updateExpandedTeam = useCallback((teamId) => {
    const newParams = new URLSearchParams(searchParams)
    
    if (teamId === expandedTeamId) {
      // Collapsing - remove expand parameter
      newParams.delete('expand')
      setExpandedTeamId(null)
    } else {
      // Expanding - set expand parameter
      newParams.set('expand', teamId.toString())
      setExpandedTeamId(teamId)
    }
    
    setSearchParams(newParams, { replace: true })
  }, [expandedTeamId, searchParams, setSearchParams])

  const { data: teamPlayers } = useQuery({
    queryKey: ['players', expandedTeamId],
    queryFn: () => fetchPlayers(expandedTeamId),
    enabled: !!expandedTeamId
  })

  const { data: teamGames } = useQuery({
    queryKey: ['games', expandedTeamId, selectedSeason],
    queryFn: () => fetchGames(expandedTeamId, null, null, selectedSeason),
    enabled: !!expandedTeamId
  })

  const handleTeamClick = (teamId) => {
    updateExpandedTeam(teamId)
  }

  const handleRefresh = async () => {
    try {
      await triggerTeamsUpdate()
      await refetchTeams()
      await queryClient.invalidateQueries({ queryKey: ['status'] })
    } catch (error) {
      console.error('Error refreshing teams:', error)
    }
  }

  if (teamsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <LoadingSpinner size="large" className="text-primary" />
        <div className="text-muted-foreground">
          {status?.is_updating && status.current_phase === 'teams' ? (
            <span>Processing team data...</span>
          ) : (
            <span>Loading teams...</span>
          )}
        </div>
      </div>
    )
  }

  if (teamsError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <p className="text-destructive">Error loading teams: {teamsError.message}</p>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['teams'] })}
          className="text-primary hover:underline"
        >
          Try again
        </button>
      </div>
    )
  }

  const sortGamesByDate = (games) => {
    if (!games) return []
    return [...games].sort((a, b) => new Date(b.game_date_utc) - new Date(a.game_date_utc))
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">NBA Teams</h1>
        <div className="flex items-center space-x-4">
          {status?.is_updating && status.current_phase === 'teams' && (
            <div className="flex items-center space-x-2 text-primary">
              <LoadingSpinner size="small" />
              <span>Updating teams...</span>
            </div>
          )}
          <button
            onClick={handleRefresh}
            disabled={isRefetching || status?.is_updating}
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
            title="Refresh teams"
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {teams?.map((team) => (
          <div key={team.team_id} className={expandedTeamId === team.team_id ? "col-span-full" : ""}>
            <button
              onClick={() => handleTeamClick(team.team_id)}
              className="w-full text-left group relative overflow-hidden rounded-lg border bg-card p-6 hover:border-primary transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className="h-20 w-20 flex-shrink-0">
                  <img
                    src={team.logo_url}
                    alt={team.name}
                    className="h-full w-full object-contain"
                  />
                </div>
                <div>
                  <h2 className="font-semibold group-hover:text-primary transition-colors">
                    {team.name}
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    {team.wins}-{team.losses}
                  </p>
                  {team.conference && team.division && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {team.conference} Conference - {team.division} Division
                    </p>
                  )}
                </div>
              </div>
            </button>

            {expandedTeamId === team.team_id && (
              <div 
                ref={expandedContentRef}
                className="mt-4 rounded-lg border bg-card p-6 space-y-6"
              >
                {/* Roster Section */}
                <div>
                  <h3 className="text-xl font-semibold mb-4">Current Roster</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {teamPlayers?.map((player) => (
                      <Link
                        key={player.player_id}
                        to={`/players/${player.player_id}`}
                        className="flex items-center space-x-3 p-3 rounded-md hover:bg-muted/50 transition-colors"
                      >
                        <img
                          src={player.headshot_url || '/default-player.svg'}
                          alt={player.full_name}
                          className="h-10 w-10 rounded-full object-cover"
                          onError={(e) => {
                            e.target.src = '/default-player.svg'
                          }}
                        />
                        <div>
                          <p className="font-medium">{player.full_name}</p>
                          <p className="text-sm text-muted-foreground">
                            {player.position} {player.jersey_number && `#${player.jersey_number}`}
                          </p>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>

                {/* Recent Games Section */}
                <div>
                  <h3 className="text-xl font-semibold mb-4">Recent Games</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {sortGamesByDate(teamGames)?.slice(0, 5).map((game) => (
                      <Link
                        key={game.game_id}
                        to={`/games/${game.game_id}`}
                        className="flex justify-between items-center p-4 rounded-md border hover:border-primary transition-colors relative"
                      >
                        {game.playoff_round && (
                          <div className="absolute top-2 right-2 bg-primary text-primary-foreground px-2 py-0.5 rounded-full text-xs font-medium">
                            {game.playoff_round}
                          </div>
                        )}
                        <div className="flex-1">
                          <div className="text-sm text-muted-foreground">
                            {format(new Date(game.game_date_utc), 'MMM d, yyyy')}
                          </div>
                          <div className="mt-1">
                            {game.home_team_id === team.team_id ? (
                              <span>vs {teams.find(t => t.team_id === game.away_team_id)?.name}</span>
                            ) : (
                              <span>@ {teams.find(t => t.team_id === game.home_team_id)?.name}</span>
                            )}
                          </div>
                        </div>
                        {game.status === 'Completed' && (
                          <div className="text-right">
                            <div className="font-semibold">
                              {game.home_team_id === team.team_id ? (
                                <span>{game.home_score} - {game.away_score}</span>
                              ) : (
                                <span>{game.away_score} - {game.home_score}</span>
                              )}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {game.home_team_id === team.team_id ? (
                                game.home_score > game.away_score ? 'W' : 'L'
                              ) : (
                                game.away_score > game.home_score ? 'W' : 'L'
                              )}
                            </div>
                          </div>
                        )}
                        {game.status === 'Upcoming' && (
                          <div className="text-sm text-muted-foreground">
                            {formatGameTime(game.game_date_utc)}
                          </div>
                        )}
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default TeamsPage