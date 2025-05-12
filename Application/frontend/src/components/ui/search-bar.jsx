import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { searchTeamsAndPlayers } from '../../services/api'
import { LoadingSpinner } from './loading-spinner'

export function SearchBar() {
  const [term, setTerm] = useState('')
  const [debouncedTerm, setDebouncedTerm] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const searchRef = useRef(null)

  // Handle clicks outside search results to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedTerm(term)
    }, 300)
    return () => clearTimeout(timer)
  }, [term])

  // Search query
  const { data: searchResults, isLoading } = useQuery({
    queryKey: ['search', debouncedTerm],
    queryFn: () => searchTeamsAndPlayers(debouncedTerm),
    enabled: debouncedTerm.length >= 2,
    staleTime: 30000 // Cache results for 30 seconds
  })

  const handleInputChange = (e) => {
    const value = e.target.value
    setTerm(value)
    setIsOpen(value.length >= 2)
  }

  const handleTeamClick = () => setIsOpen(false)
  const handlePlayerClick = () => setIsOpen(false)

  return (
    <div className="relative w-64" ref={searchRef}>
      <div className="relative">
        <input
          type="text"
          value={term}
          onChange={handleInputChange}
          placeholder="Search teams and players..."
          className="w-full rounded-lg border px-3 py-2 pr-8 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary"
        />
        {debouncedTerm.length >= 2 && isLoading && (
          <div className="absolute right-2 top-1/2 -translate-y-1/2">
            <LoadingSpinner size="small" />
          </div>
        )}
      </div>

      {isOpen && searchResults && searchResults.length > 0 && (
        <div className="absolute mt-1 w-full rounded-lg border bg-background shadow-lg">
          <div className="max-h-96 overflow-auto p-2">
            {searchResults.map((result) => (
              <div key={result.team.team_id} className="mb-4 last:mb-0">
                <Link
                  to={`/teams/${result.team.team_id}`}
                  onClick={handleTeamClick}
                  className="flex items-center space-x-2 rounded-md p-2 hover:bg-muted"
                >
                  <img
                    src={result.team.logo_url}
                    alt={result.team.name}
                    className="h-6 w-6 object-contain"
                    onError={(e) => {
                      e.target.src = '/default-team.png'
                    }}
                  />
                  <span className="font-medium">{result.team.name}</span>
                </Link>

                {result.players.length > 0 && (
                  <div className="ml-8 mt-1 space-y-1">
                    {result.players.map((player) => (
                      <Link
                        key={player.player_id}
                        to={`/players/${player.player_id}`}
                        onClick={handlePlayerClick}
                        className="flex items-center justify-between rounded-md p-2 text-sm hover:bg-muted"
                      >
                        <span>{player.full_name}</span>
                        {player.traded_date && player.previous_team_id && player.previous_team_id !== player.current_team_id && (
                          <span className="text-xs text-muted-foreground">Recently Traded</span>
                        )}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {isOpen && searchResults && searchResults.length === 0 && debouncedTerm.length >= 2 && (
        <div className="absolute mt-1 w-full rounded-lg border bg-background p-4 text-center text-sm text-muted-foreground">
          No results found
        </div>
      )}
    </div>
  )
}