import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { fetchStatus } from '../../services/api';
import { LoadingSpinner } from '../ui/loading-spinner';
import { SearchBar } from '../ui/search-bar';
import { Button } from '../ui/button';
import { useState, useRef, useEffect } from 'react';

export default function NavigationBar() {
  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: fetchStatus,
  });
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
    const date = new Date(dateStr);
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return `${format(date, 'MMM d, HH:mm')}`;
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

    if (status.last_error) {
      return (
        <div className="flex items-center space-x-2 text-destructive">
          <span>Error</span>
          <ChevronIcon expanded={showStatusDropdown} />
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
            <div className="text-sm text-muted-foreground">{formatDate(status.last_update)} ({Intl.DateTimeFormat().resolvedOptions().timeZone})</div>
          </div>
          <div>
            <div className="text-sm font-medium">Next Update</div>
            <div className="text-sm text-muted-foreground">{formatDate(status.next_update)} ({Intl.DateTimeFormat().resolvedOptions().timeZone})</div>
          </div>
          {status.last_error && (
            <div>
              <div className="text-sm font-medium text-destructive">Last Error</div>
              <div className="text-sm text-destructive">{status.last_error}</div>
              <div className="text-xs text-muted-foreground">({formatDate(status.last_error_time)})</div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-lg border-b border-border/40 bg-background/95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="text-xl font-bold text-primary">
              NBA Stats
            </Link>
            <div className="hidden md:flex space-x-4">
              <Link to="/games" className="nav-link">
                Games
              </Link>
              <Link to="/upcoming-games" className="nav-link">
                Upcoming Games
              </Link>
              <Link to="/teams" className="nav-link">
                Teams
              </Link>
              <Link to="/players" className="nav-link">
                Players
              </Link>
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-4">
            <SearchBar />
            <div className="relative" ref={dropdownRef}>
              <Button
                variant="ghost"
                size="sm"
                className="relative"
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