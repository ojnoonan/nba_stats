// Always use relative path for API URL
const API_BASE_URL = '/api'

const RETRY_COUNT = 3
const RETRY_DELAY = 1000
const REQUEST_TIMEOUT = 15000

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

const fetchWithRetry = async (url, options = {}) => {
  let lastError
  
  for (let i = 0; i < RETRY_COUNT; i++) {
    try {
      const cleanUrl = url.replace(/\/+$/, '')
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT)
      
      const response = await fetch(cleanUrl, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        throw new ApiError(`HTTP error: ${response.status}`, response.status)
      }
      
      const data = await response.json()
      return data
    } catch (error) {
      lastError = error
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
        throw error // Don't retry client errors
      }
      if (i < RETRY_COUNT - 1) {
        await sleep(RETRY_DELAY * Math.pow(2, i))
        continue
      }
    }
  }
  
  throw lastError
}

export const fetchTeams = async () => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/teams`)
  } catch (error) {
    console.error('Failed to fetch teams:', error)
    throw new Error('Failed to fetch teams')
  }
}

export const fetchTeam = async (teamId) => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/teams/${teamId}`)
  } catch (error) {
    console.error('Failed to fetch team:', error)
    throw new Error('Failed to fetch team')
  }
}

export const fetchPlayers = async (teamId = null, activeOnly = true) => {
  try {
    const params = new URLSearchParams()
    if (teamId) params.append('team_id', teamId)
    if (activeOnly) params.append('active_only', activeOnly)
    
    const url = `${API_BASE_URL}/players${params.toString() ? `?${params}` : ''}`
    return await fetchWithRetry(url)
  } catch (error) {
    console.error('Failed to fetch players:', error)
    throw new Error('Failed to fetch players')
  }
}

export const fetchPlayer = async (playerId) => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/players/${playerId}`)
  } catch (error) {
    console.error('Failed to fetch player:', error)
    throw new Error('Failed to fetch player')
  }
}

export const fetchPlayerStats = async (playerId, limit = null, season = null) => {
  try {
    const params = new URLSearchParams()
    if (limit) params.append('limit', limit)
    if (season) params.append('season', season)
    
    const url = `${API_BASE_URL}/players/${playerId}/stats${params.toString() ? `?${params}` : ''}`
    return await fetchWithRetry(url)
  } catch (error) {
    console.error('Failed to fetch player stats:', error)
    throw new Error('Failed to fetch player stats')
  }
}

export const fetchGames = async (teamId = null, status = null, playerId = null, season = null) => {
  try {
    const params = new URLSearchParams()
    if (teamId) params.append('team_id', teamId)
    if (status) params.append('status', status)
    if (playerId) params.append('player_id', playerId)
    if (season) params.append('season', season)
    
    const url = `${API_BASE_URL}/games${params.toString() ? `?${params}` : ''}`
    return await fetchWithRetry(url)
  } catch (error) {
    console.error('Failed to fetch games:', error)
    throw new Error('Failed to fetch games')
  }
}

export const fetchGame = async (gameId) => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/games/${gameId}`)
  } catch (error) {
    console.error('Failed to fetch game:', error)
    throw new Error('Failed to fetch game')
  }
}

export const fetchGameStats = async (gameId) => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/games/${gameId}/stats`)
  } catch (error) {
    console.error('Failed to fetch game stats:', error)
    throw new Error('Failed to fetch game stats')
  }
}

export const fetchStatus = async () => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/status`)
  } catch (error) {
    console.error('Failed to fetch update status:', error)
    throw new Error('Failed to fetch update status')
  }
}

export const triggerUpdate = async (types = null) => {
  try {
    const url = `${API_BASE_URL}/update`
    const options = {
      method: 'POST'
    }
    
    if (types && types.length > 0) {
      options.headers = {
        'Content-Type': 'application/json'
      }
      options.body = JSON.stringify({ update_types: types })
    }
    
    return await fetchWithRetry(url, options)
  } catch (error) {
    console.error('Failed to trigger update:', error)
    throw new Error('Failed to trigger update')
  }
}

export const triggerGamesUpdate = async () => {
  return triggerUpdate(['games'])
}

export const triggerTeamsUpdate = async () => {
  return triggerUpdate(['teams'])
}

export const triggerPlayersUpdate = async () => {
  return triggerUpdate(['players'])
}

export const cancelUpdate = async () => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/reset-update-status`, {
      method: 'POST'
    })
  } catch (error) {
    console.error('Failed to cancel update:', error)
    throw new Error('Failed to cancel update')
  }
}

export const cancelAdminUpdate = async () => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/admin/update/cancel`, {
      method: 'POST'
    });
  } catch (error) {
    console.error('Failed to cancel admin update:', error);
    throw new Error('Failed to cancel admin update');
  }
};

export const searchTeamsAndPlayers = async (term, season = null) => {
  try {
    const params = new URLSearchParams({ term })
    if (season) params.append('season', season)
    return await fetchWithRetry(`${API_BASE_URL}/search?${params}`)
  } catch (error) {
    console.error('Failed to search:', error)
    throw new Error('Failed to search')
  }
}

export const fetchAdminStatus = async () => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/admin/status`)
  } catch (error) {
    console.error('Failed to fetch admin status:', error)
    throw new Error('Failed to fetch admin status')
  }
}

export const triggerFullUpdate = async () => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/admin/update/all`, {
      method: 'POST'
    })
  } catch (error) {
    console.error('Failed to trigger full update:', error)
    throw new Error('Failed to trigger full update')
  }
}

export const triggerComponentUpdate = async (component) => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/admin/update/${component}`, {
      method: 'POST'
    })
  } catch (error) {
    console.error('Failed to trigger component update:', error)
    throw new Error('Failed to trigger component update')
  }
}

export const fetchAvailableSeasons = async () => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/games/seasons`)
  } catch (error) {
    console.error('Failed to fetch available seasons:', error)
    throw new Error('Failed to fetch available seasons')
  }
}

export const fetchPlayerLastXGames = async (playerId, count = 5, season = null) => {
  try {
    const params = new URLSearchParams()
    params.append('count', count)
    if (season) params.append('season', season)
    
    const url = `${API_BASE_URL}/players/${playerId}/last_x_games?${params}`
    return await fetchWithRetry(url)
  } catch (error) {
    console.error('Failed to fetch player last X games:', error)
    throw new Error('Failed to fetch player last X games')
  }
}

export const fetchPlayerHighLowGames = async (playerId, count = 5, season = null) => {
  try {
    const params = new URLSearchParams()
    params.append('count', count)
    if (season) params.append('season', season)
    
    const url = `${API_BASE_URL}/players/${playerId}/high_low_games?${params}`
    return await fetchWithRetry(url)
  } catch (error) {
    console.error('Failed to fetch player high/low games:', error)
    throw new Error('Failed to fetch player high/low games')
  }
}