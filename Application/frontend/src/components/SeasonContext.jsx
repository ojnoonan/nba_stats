import React, { createContext, useContext, useState, useEffect } from 'react'
import { fetchAvailableSeasons } from '../services/api'

const SeasonContext = createContext()

export const useSeason = () => {
  const context = useContext(SeasonContext)
  if (!context) {
    throw new Error('useSeason must be used within a SeasonProvider')
  }
  return context
}

const getCurrentSeason = () => {
  const today = new Date()
  const year = today.getFullYear()
  const month = today.getMonth() + 1
  
  // NBA season typically starts in October
  if (month >= 10) {
    return `${year}-${String(year + 1).slice(-2)}`
  } else {
    return `${year - 1}-${String(year).slice(-2)}`
  }
}

export const SeasonProvider = ({ children }) => {
  const [selectedSeason, setSelectedSeason] = useState(null)
  const [availableSeasons, setAvailableSeasons] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadSeasons = async () => {
      try {
        setLoading(true)
        const seasons = await fetchAvailableSeasons()
        setAvailableSeasons(seasons)
        
        // Check if there's a saved season in localStorage
        const savedSeason = localStorage.getItem('selectedSeason')
        
        if (savedSeason && seasons.includes(savedSeason)) {
          setSelectedSeason(savedSeason)
        } else if (seasons.length > 0) {
          // Default to current season if available, otherwise most recent
          const currentSeason = getCurrentSeason()
          const defaultSeason = seasons.includes(currentSeason) ? currentSeason : seasons[0]
          setSelectedSeason(defaultSeason)
        }
      } catch (err) {
        setError(err.message)
        console.error('Failed to load seasons:', err)
      } finally {
        setLoading(false)
      }
    }

    loadSeasons()
  }, [])

  const changeSeason = (season) => {
    setSelectedSeason(season)
    // Save to localStorage
    if (season) {
      localStorage.setItem('selectedSeason', season)
    } else {
      localStorage.removeItem('selectedSeason')
    }
  }

  const isCurrentSeason = (season) => {
    return season === getCurrentSeason()
  }

  const value = {
    selectedSeason,
    availableSeasons,
    loading,
    error,
    changeSeason,
    isCurrentSeason,
    getCurrentSeason
  }

  return (
    <SeasonContext.Provider value={value}>
      {children}
    </SeasonContext.Provider>
  )
}

export default SeasonContext
