import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { fetchPlayers, fetchTeams, fetchStatus, fetchPlayerStats, fetchPlayer, triggerPlayersUpdate } from '../services/api'
import { LoadingSpinner } from '../components/ui/loading-spinner'
import { format } from 'date-fns'
import { Tooltip, TooltipWrapper } from '../components/ui/tooltip'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { useState } from 'react'
import { useSeason } from '../components/SeasonContext'

const PlayersPage = () => {
  const queryClient = useQueryClient()
  const { id } = useParams()
  const [sorting, setSorting] = useState([])
  const { selectedSeason } = useSeason()

  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: fetchStatus
  })

  const { data: players, isLoading: playersLoading, error: playersError, isFetching: isRefetching, refetch: refetchPlayers } = useQuery({
    queryKey: ['players', id],
    queryFn: () => id ? fetchPlayer(id) : fetchPlayers(null, true)
  })

  const { data: playerStats, isLoading: statsLoading } = useQuery({
    queryKey: ['playerStats', id, selectedSeason],
    queryFn: () => fetchPlayerStats(id, selectedSeason),
    enabled: !!id
  })

  const { data: teams, isLoading: teamsLoading, error: teamsError } = useQuery({
    queryKey: ['teams'],
    queryFn: fetchTeams
  })

  const getStatusText = () => {
    if (isRefetching && status?.is_updating) return 'Fetching & Processing players...'
    if (isRefetching) return 'Fetching new player data...'
    if (status?.is_updating && status.current_phase === 'players') return 'Processing player updates...'
    return null
  }

  const handleRefresh = async () => {
    try {
      await triggerPlayersUpdate()
      await refetchPlayers()
      await queryClient.invalidateQueries({ queryKey: ['status'] })
    } catch (error) {
      console.error('Error refreshing players:', error)
    }
  }

  const columnHelper = createColumnHelper()
  const columns = [
    columnHelper.accessor('game_date_utc', {
      header: 'Date',
      cell: info => (
        <div className="text-left">
          {info.getValue() ? format(new Date(info.getValue()), 'MMM d, yyyy') : 'N/A'}
        </div>
      ),
      sortingFn: 'datetime'
    }),
    columnHelper.accessor(row => ({
      teamName: row.opposition_team_name,
      teamId: row.opposition_team_id,
      isHome: row.is_home_game
    }), {
      id: 'opposition',
      header: 'Opponent',
      cell: info => {
        const val = info.getValue()
        if (!val || !val.teamName) return '-'
        
        return (
          <div className="text-left">
            {val.teamId ? (
              <Link 
                to={`/teams?expand=${val.teamId}`}
                className="text-primary hover:underline"
              >
                {val.teamName}
              </Link>
            ) : (
              val.teamName
            )}
          </div>
        )
      }
    }),
    columnHelper.accessor('minutes', {
      header: () => (
        <Tooltip content="Minutes Played">
          <span>MIN</span>
        </Tooltip>
      ),
      cell: info => info.getValue() || '-'
    }),
    columnHelper.accessor('points', {
      header: () => (
        <Tooltip content="Points Scored">
          <span>PTS</span>
        </Tooltip>
      ),
      cell: info => info.getValue() || '-',
      sortingFn: 'number'
    }),
    columnHelper.accessor('rebounds', {
      header: () => (
        <Tooltip content="Total Rebounds (Offensive + Defensive)">
          <span>REB</span>
        </Tooltip>
      ),
      cell: info => info.getValue() || '-',
      sortingFn: 'number'
    }),
    columnHelper.accessor('assists', {
      header: () => (
        <Tooltip content="Assists - Passes that lead directly to a made basket">
          <span>AST</span>
        </Tooltip>
      ),
      cell: info => info.getValue() || '-',
      sortingFn: 'number'
    }),
    columnHelper.accessor('steals', {
      header: () => (
        <Tooltip content="Steals - Taking the ball from an opposing player">
          <span>STL</span>
        </Tooltip>
      ),
      cell: info => info.getValue() || '-',
      sortingFn: 'number'
    }),
    columnHelper.accessor('blocks', {
      header: () => (
        <Tooltip content="Blocks - Deflecting an opposing player's shot attempt">
          <span>BLK</span>
        </Tooltip>
      ),
      cell: info => info.getValue() || '-',
      sortingFn: 'number'
    }),
    columnHelper.accessor(row => ({
      made: row.fgm,
      attempts: row.fga,
      pct: row.fg_pct
    }), {
      id: 'fg',
      header: () => (
        <Tooltip content="Field Goals - All shot attempts (Made-Attempted)">
          <span>FG</span>
        </Tooltip>
      ),
      cell: info => {
        const val = info.getValue()
        return val ? `${val.made}-${val.attempts} (${(val.pct * 100).toFixed(1)}%)` : '-'
      }
    }),
    columnHelper.accessor(row => ({
      made: row.tpm,
      attempts: row.tpa,
      pct: row.tp_pct
    }), {
      id: '3p',
      header: () => (
        <Tooltip content="Three Point Field Goals - Shots from beyond the 3-point line (Made-Attempted)">
          <span>3P</span>
        </Tooltip>
      ),
      cell: info => {
        const val = info.getValue()
        return val ? `${val.made}-${val.attempts} (${(val.pct * 100).toFixed(1)}%)` : '-'
      }
    }),
    columnHelper.accessor(row => ({
      made: row.ftm,
      attempts: row.fta,
      pct: row.ft_pct
    }), {
      id: 'ft',
      header: () => (
        <Tooltip content="Free Throws - Uncontested shots awarded after a foul (Made-Attempted)">
          <span>FT</span>
        </Tooltip>
      ),
      cell: info => {
        const val = info.getValue()
        return val ? `${val.made}-${val.attempts} (${(val.pct * 100).toFixed(1)}%)` : '-'
      }
    }),
    columnHelper.accessor('turnovers', {
      header: () => (
        <Tooltip content="Turnovers - Lost possession of the ball to the opposing team">
          <span>TO</span>
        </Tooltip>
      ),
      cell: info => info.getValue() || '-',
      sortingFn: 'number'
    }),
    columnHelper.accessor('plus_minus', {
      header: () => (
        <Tooltip content="Plus/Minus - Point differential while the player was on the court">
          <span>+/-</span>
        </Tooltip>
      ),
      cell: info => {
        const val = info.getValue()
        if (val === null || val === undefined) return '-'
        
        const displayValue = val > 0 ? `+${val}` : val
        const colorClass = val > 0 ? 'text-green-500' : val < 0 ? 'text-red-500' : ''
        
        return (
          <span className={colorClass}>
            {displayValue}
          </span>
        )
      },
      sortingFn: 'number'
    })
  ]

  const table = useReactTable({
    data: playerStats || [],
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  // Only show loading spinner if players are loading, not teams
  if (playersLoading || (!players?.length && !id) || (id && !players)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <LoadingSpinner size="large" className="text-primary" />
        <div className="text-muted-foreground">
          {status?.is_updating && status.current_phase === 'players' ? (
            <span>Processing player data...</span>
          ) : (
            <span>Loading players...</span>
          )}
        </div>
      </div>
    )
  }

  // Only show error page if players fail to load, not teams
  if (playersError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <p className="text-destructive">Error loading players: {playersError.message}</p>
        <button
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['players'] })
          }}
          className="text-primary hover:underline"
        >
          Try again
        </button>
      </div>
    )
  }

  const getTeamName = (teamId) => {
    const team = teams?.find(t => t.team_id === teamId)
    return team?.name || 'Free Agent'
  }

  if (id) {
    const player = Array.isArray(players) ? players[0] : players
    if (!player) return <div>Player not found</div>

    const calculateAverages = (stats) => {
      if (!stats?.length) return null
      const totals = stats.reduce((acc, stat) => ({
        games: acc.games + 1,
        points: acc.points + (stat.points || 0),
        rebounds: acc.rebounds + (stat.rebounds || 0),
        assists: acc.assists + (stat.assists || 0),
        steals: acc.steals + (stat.steals || 0),
        blocks: acc.blocks + (stat.blocks || 0)
      }), { games: 0, points: 0, rebounds: 0, assists: 0, steals: 0, blocks: 0 })

      return {
        ppg: (totals.points / totals.games).toFixed(1),
        rpg: (totals.rebounds / totals.games).toFixed(1),
        apg: (totals.assists / totals.games).toFixed(1),
        spg: (totals.steals / totals.games).toFixed(1),
        bpg: (totals.blocks / totals.games).toFixed(1)
      }
    }

    const averages = calculateAverages(playerStats)

    // Use selected season from context instead of calculating current season
    const season = selectedSeason || 'Current Season'

    return (
      <TooltipWrapper>
        <div className="space-y-6">
          <div className="flex items-center space-x-4 mb-6">
            <Link to="/players" className="text-primary hover:underline">&larr; Back to Players</Link>
          </div>
          <div className="bg-card p-8 rounded-lg border">
            <div className="flex flex-col md:flex-row items-center md:items-start space-y-6 md:space-y-0 md:space-x-8">
              <div className="h-48 w-48 flex-shrink-0 relative">
                <img
                  src={player.headshot_url || '/default-player.svg'}
                  alt={player.full_name}
                  className="h-full w-full object-cover rounded-full"
                  onError={(e) => {
                    e.target.src = '/default-player.svg'
                  }}
                />
                {player.traded_date && player.previous_team_id && player.previous_team_id !== player.current_team_id && (
                  <div className="absolute -top-2 -right-2 bg-primary text-primary-foreground px-3 py-1 rounded-full text-sm font-medium shadow-lg">
                    Recently Traded
                  </div>
                )}
              </div>
              <div className="flex-1 text-center md:text-left">
                <h1 className="text-4xl font-bold mb-4">{player.full_name}</h1>
                <div className="space-y-2">
                  <p className="text-lg">
                    <span className="font-semibold">Current Team:</span>{' '}
                    {player.current_team_id ? (
                      <Link 
                        to={`/teams?expand=${player.current_team_id}`} 
                        className="text-primary hover:underline"
                      >
                        {getTeamName(player.current_team_id)}
                      </Link>
                    ) : (
                      'Free Agent'
                    )}
                  </p>
                  {player.traded_date && player.previous_team_id && player.previous_team_id !== player.current_team_id && (
                    <p className="text-lg text-muted-foreground">
                      Traded from {getTeamName(player.previous_team_id)} on {format(new Date(player.traded_date), 'MMM d, yyyy')}
                    </p>
                  )}
                  {player.position && (
                    <p className="text-lg">
                      <span className="font-semibold">Position:</span> {player.position}
                    </p>
                  )}
                  {player.jersey_number && (
                    <p className="text-lg">
                      <span className="font-semibold">Jersey Number:</span> {parseInt(player.jersey_number)}
                    </p>
                  )}
                  <p className="text-lg">
                    <span className="font-semibold">Status:</span> {player.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>

                {averages && (
                  <div className="mt-8">
                    <h2 className="text-xl font-semibold mb-4">{season} Season Averages</h2>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="stat-card">
                        <h3 className="text-sm font-medium text-muted-foreground">PPG</h3>
                        <p className="stat-value">{averages.ppg}</p>
                      </div>
                      <div className="stat-card">
                        <h3 className="text-sm font-medium text-muted-foreground">RPG</h3>
                        <p className="stat-value">{averages.rpg}</p>
                      </div>
                      <div className="stat-card">
                        <h3 className="text-sm font-medium text-muted-foreground">APG</h3>
                        <p className="stat-value">{averages.apg}</p>
                      </div>
                      <div className="stat-card">
                        <h3 className="text-sm font-medium text-muted-foreground">SPG</h3>
                        <p className="stat-value">{averages.spg}</p>
                      </div>
                      <div className="stat-card">
                        <h3 className="text-sm font-medium text-muted-foreground">BPG</h3>
                        <p className="stat-value">{averages.bpg}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">Recent Games</h2>
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted">
                  {table.getHeaderGroups().map(headerGroup => (
                    <tr key={headerGroup.id}>
                      {headerGroup.headers.map(header => (
                        <th 
                          key={header.id}
                          className="px-4 py-3 text-left text-sm font-medium text-muted-foreground relative overflow-visible"
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          <div className="flex items-center space-x-2 cursor-pointer">
                            {flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                            {{
                              asc: ' ↑',
                              desc: ' ↓',
                            }[header.column.getIsSorted()] ?? null}
                          </div>
                        </th>
                      ))}
                    </tr>
                  ))}
                </thead>
                <tbody>
                  {table.getRowModel().rows.map(row => (
                    <tr 
                      key={row.id}
                      className="border-t border-border hover:bg-muted/50 transition-colors"
                    >
                      {row.getVisibleCells().map(cell => (
                        <td key={cell.id} className="px-4 py-3 text-sm">
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </TooltipWrapper>
    )
  }

  const groupPlayersByTeam = () => {
    const grouped = {}
    
    if (!players?.length) {
      return grouped
    }
    
    // Group by teams first if teams data is available
    if (teams?.length > 0) {
      // Sort teams alphabetically for consistent display order
      const sortedTeams = [...teams].sort((a, b) => a.name.localeCompare(b.name))
      sortedTeams.forEach(team => {
        const teamPlayers = players.filter(player => player.current_team_id === team.team_id)
        if (teamPlayers.length > 0) {
          grouped[team.name] = teamPlayers
        }
      })
    } else if (!teamsLoading) {
      // If teams failed to load, show all players with team IDs as "Unknown Team"
      const playersWithTeams = players.filter(player => player.current_team_id)
      if (playersWithTeams.length > 0) {
        grouped['Players (Team info unavailable)'] = playersWithTeams
      }
    }
    
    // Add free agents at the end
    const freeAgents = players.filter(player => !player.current_team_id)
    if (freeAgents.length > 0) {
      grouped['Free Agents'] = freeAgents
    }

    return grouped
  }

  const groupedPlayers = groupPlayersByTeam()

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">NBA Players</h1>
          <p className="text-muted-foreground mt-1">
            {selectedSeason || 'Current Season'} Season
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {getStatusText() && (
            <div className="flex items-center space-x-2 text-primary">
              <LoadingSpinner size="small" />
              <span>{getStatusText()}</span>
            </div>
          )}
          <button
            onClick={handleRefresh}
            disabled={isRefetching || status?.is_updating}
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
            title="Refresh players"
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

      <div className="space-y-8">
        {teamsLoading && (
          <div className="text-center py-4">
            <div className="flex items-center justify-center space-x-2 text-muted-foreground">
              <LoadingSpinner size="small" />
              <span>Loading team information...</span>
            </div>
          </div>
        )}
        {teamsError && (
          <div className="text-center py-4">
            <p className="text-destructive">Error loading teams: {teamsError.message}</p>
            <p className="text-sm text-muted-foreground mt-1">Players will be shown without team grouping</p>
          </div>
        )}
        {Object.entries(groupedPlayers).map(([teamName, teamPlayers]) => (
          teamPlayers.length > 0 && (
            <div key={teamName} className="space-y-4">
              <h2 className="text-2xl font-semibold border-b pb-2">{teamName} ({teamPlayers.length} players)</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {teamPlayers.map((player) => (
                  <Link
                    key={player.player_id}
                    to={`/players/${player.player_id}`}
                    className="group relative overflow-hidden rounded-lg border bg-card p-6 hover:border-primary transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="h-20 w-20 flex-shrink-0">
                        <img
                          src={player.headshot_url || '/default-player.svg'}
                          alt={player.full_name}
                          className="h-full w-full object-cover rounded-full"
                          onError={(e) => {
                            e.target.src = '/default-player.svg'
                          }}
                        />
                      </div>
                      <div>
                        <h2 className="font-semibold group-hover:text-primary transition-colors">
                          {player.full_name}
                        </h2>
                        {player.position && (
                          <p className="text-sm mt-1">
                            Position: {player.position}
                          </p>
                        )}
                        {player.jersey_number && (
                          <p className="text-sm">
                            #{player.jersey_number}
                          </p>
                        )}
                      </div>
                    </div>
                    {player.traded_date && player.previous_team_id && player.previous_team_id !== player.current_team_id && (
                      <div className="absolute -top-2 -right-2 bg-primary text-primary-foreground px-2 py-1 rounded-full text-xs font-medium shadow-lg">
                        Traded
                      </div>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          )
        ))}
        {Object.keys(groupedPlayers).length === 0 && (
          <div className="text-center py-8">
            <p className="text-muted-foreground">No players found or still loading...</p>
            <p className="text-sm text-muted-foreground mt-2">
              Players: {players?.length || 0}, Teams: {teams?.length || 0}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default PlayersPage