import React, { useState, useEffect } from 'react'
import { fetchAvailableSeasons } from '../services/api'

const SeasonSelector = ({ selectedSeason, onSeasonChange, className = "" }) => {
  const [seasons, setSeasons] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadSeasons = async () => {
      try {
        setLoading(true)
        const availableSeasons = await fetchAvailableSeasons()
        setSeasons(availableSeasons)
        
        // If no season is selected and we have seasons, select the most recent one
        if (!selectedSeason && availableSeasons.length > 0) {
          onSeasonChange(availableSeasons[0]) // Seasons are ordered desc, so first is most recent
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadSeasons()
  }, [selectedSeason, onSeasonChange])

  const getCurrentSeason = () => {
    const today = new Date()
    const year = today.getFullYear()
    const month = today.getMonth() + 1 // getMonth() returns 0-based month
    
    // NBA season typically starts in October (month 10)
    if (month >= 10) {
      return `${year}-${String(year + 1).slice(-2)}`
    } else {
      return `${year - 1}-${String(year).slice(-2)}`
    }
  }

  const formatSeasonDisplay = (season) => {
    if (!season) return ""
    const parts = season.split('-')
    if (parts.length === 2) {
      return `${parts[0]}-${parts[1]}`
    }
    return season
  }

  if (loading) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <span className="text-sm text-muted-foreground">Loading seasons...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <span className="text-sm text-destructive">Error loading seasons</span>
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      <label htmlFor="season-select" className="absolute -top-4 left-0 text-xs text-gray-400 whitespace-nowrap">
        Season
      </label>
      <select
        id="season-select"
        value={selectedSeason || ''}
        onChange={(e) => onSeasonChange(e.target.value)}
        className="h-10 px-3 py-2 text-sm border border-gray-700 rounded-md bg-gray-900 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent hover:border-gray-600 transition-colors duration-200"
      >
        {seasons.map((season) => (
          <option key={season} value={season} className="bg-gray-900 text-white">
            {formatSeasonDisplay(season)}
            {season === getCurrentSeason() && ' (Current)'}
          </option>
        ))}
      </select>
    </div>
  )
}

export default SeasonSelector
