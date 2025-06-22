import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { fetchStatus } from '../../services/api';
import { LoadingSpinner } from '../ui/loading-spinner';
import { SearchBar } from '../ui/search-bar';
import { Button } from '../ui/button';
import { useSeason } from '../SeasonContext';
import { useState, useRef, useEffect } from 'react';

export default function NavigationBar() {
  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: fetchStatus,
    refetchInterval: (data) => (data?.is_updating ? 1000 : 5000), // Refetch every second during updates, every 5 seconds otherwise
  });
  const { selectedSeason } = useSeason();
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowStatusDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    
    // Check if the timestamp already has timezone information
    const hasTimezone = dateStr.includes('Z') || 
                       dateStr.includes('+') || 
                       (dateStr.includes('T') && dateStr.includes('-', dateStr.indexOf('T')));
    
    // If no timezone info, append 'Z' to treat as UTC
    const utcDateString = hasTimezone ? dateStr : dateStr + 'Z';
    
    const date = new Date(utcDateString);
    return `${format(date, 'MMM d, yyyy')}`;
  };

  const formatDateWithTime = (dateStr) => {
    if (!dateStr) return 'N/A';
    
    // Check if the timestamp already has timezone information
    const hasTimezone = dateStr.includes('Z') || 
                       dateStr.includes('+') || 
                       (dateStr.includes('T') && dateStr.includes('-', dateStr.indexOf('T')));
    
    // If no timezone info, append 'Z' to treat as UTC
    const utcDateString = hasTimezone ? dateStr : dateStr + 'Z';
    
    const date = new Date(utcDateString);
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return `${format(date, 'MMM d, yyyy HH:mm')}`;
  };

  const renderStatusMessage = () => {
    if (!status) return null;

    if (status.is_updating) {
      const phase = status.current_phase || 'data';
      return (
        <div className="flex items-center space-x-2 text-primary">
          <LoadingSpinner size="small" />
          <span>Updating {phase}</span>
        </div>
      );
    }

    return (
      <div className="flex items-center space-x-2">
        <span>Updated {formatDate(status.last_update)}</span>
        <ChevronIcon expanded={showStatusDropdown} />
      </div>
    );
  };

  const renderStatusDropdown = () => {
    if (!status || status.is_updating) return null;

    return (
      <div className="absolute right-0 top-full mt-1 w-72 rounded-lg border bg-background shadow-lg p-4">
        <div className="space-y-3">
          <div>
            <div className="text-sm font-medium">Last Update</div>
            <div className="text-sm text-muted-foreground">{formatDateWithTime(status.last_update)} ({Intl.DateTimeFormat().resolvedOptions().timeZone})</div>
          </div>
          <div>
            <div className="text-sm font-medium">Next Update</div>
            <div className="text-sm text-muted-foreground">{formatDateWithTime(status.next_update)} ({Intl.DateTimeFormat().resolvedOptions().timeZone})</div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-lg border-b border-border/40 bg-background/95">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-x-8 lg:gap-x-10">
            <Link to="/" className="text-xl font-bold text-white hover:text-gray-200 transition-colors duration-200">
              NBA Stats
            </Link>
            <div className="hidden md:flex items-stretch flex-nowrap gap-x-2 h-16">
              <div className="flex items-center px-3 hover:bg-gray-700 transition-colors duration-150 cursor-pointer">
                <Link 
                  to="/games" 
                  className="text-sm text-white whitespace-nowrap"
                >
                  Games
                </Link>
              </div>
              <div className="flex items-center px-3 hover:bg-gray-700 transition-colors duration-150 cursor-pointer">
                <Link 
                  to="/upcoming-games" 
                  className="text-sm text-white whitespace-nowrap"
                >
                  Upcoming Games
                </Link>
              </div>
              <div className="flex items-center px-3 hover:bg-gray-700 transition-colors duration-150 cursor-pointer">
                <Link 
                  to="/teams" 
                  className="text-sm text-white whitespace-nowrap"
                >
                  Teams
                </Link>
              </div>
              <div className="flex items-center px-3 hover:bg-gray-700 transition-colors duration-150 cursor-pointer">
                <Link 
                  to="/players" 
                  className="text-sm text-white whitespace-nowrap"
                >
                  Players
                </Link>
              </div>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-x-4 h-16">
            <div className="flex items-center h-16">
              <SearchBar />
            </div>
            <div className="relative flex items-center h-16" ref={dropdownRef}>
              <Button
                variant="ghost"
                size="sm"
                className="relative h-10 text-white hover:text-gray-300 bg-transparent hover:bg-gray-700 rounded-md px-2 py-2 transition-colors duration-150"
                onClick={() => !status?.is_updating && setShowStatusDropdown(!showStatusDropdown)}
                disabled={status?.is_updating}
              >
                {renderStatusMessage()}
              </Button>
              {showStatusDropdown && renderStatusDropdown()}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

function ChevronIcon({ expanded }) {
  return (
    <svg
      className={`h-4 w-4 transition-transform ${expanded ? 'rotate-180' : ''}`}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 9l-7 7-7-7"
      />
    </svg>
  );
}