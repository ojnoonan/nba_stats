import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { 
  fetchTeams, 
  fetchPlayers, 
  fetchGames, 
  fetchStatus 
} from '../services/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { LoadingSpinner } from '../components/ui/loading-spinner';
import { useSeason } from '../components/SeasonContext';
import SeasonSelector from '../components/SeasonSelector';

const HomePage = () => {
  const { selectedSeason, changeSeason } = useSeason();
  const { 
    data: teams,
    isFetching: isRefetchingTeams
  } = useQuery({
    queryKey: ['teams'],
    queryFn: fetchTeams
  });

  const { 
    data: players,
    isFetching: isRefetchingPlayers 
  } = useQuery({
    queryKey: ['players'],
    queryFn: () => fetchPlayers(null, true)
  });

  const { 
    data: games,
    isFetching: isRefetchingGames
  } = useQuery({
    queryKey: ['games', selectedSeason],
    queryFn: () => fetchGames(null, null, null, selectedSeason)
  });

  const {
    data: status
  } = useQuery({
    queryKey: ['status'],
    queryFn: fetchStatus,
    refetchInterval: 5000
  });

  const sections = [
    {
      title: 'Teams',
      count: teams?.length || 0,
      path: '/teams',
      isLoading: status?.is_updating && status.current_phase === 'teams',
      isRefetching: isRefetchingTeams,
      description: 'Browse NBA teams and their standings'
    },
    {
      title: 'Players',
      count: players?.length || 0,
      path: '/players',
      isLoading: status?.is_updating && status.current_phase === 'players',
      isRefetching: isRefetchingPlayers,
      description: 'Browse player profiles and statistics'
    },
    {
      title: 'Games',
      count: games?.length || 0,
      path: '/games',
      isLoading: status?.is_updating && status.current_phase === 'games',
      isRefetching: isRefetchingGames,
      description: 'View all NBA game results and details'
    },
    {
      title: 'Upcoming Games',
      count: games?.filter(game => game.status === 'Upcoming').length || 0,
      path: '/upcoming-games',
      isLoading: status?.is_updating && status.current_phase === 'games',
      isRefetching: isRefetchingGames,
      description: 'Check upcoming NBA game schedules'
    }
  ];

  const isAnySectionLoading = sections.some(s => s.isRefetching && (s.count === 0));

  return (
    <div className="space-y-8 container mx-auto p-4">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="text-left">
            <h1 className="text-3xl font-bold">NBA Stats Dashboard</h1>
            <p className="text-muted-foreground">
              Last successful data update: {status?.last_update ? (() => {
                // Check if the timestamp already has timezone information
                const hasTimezone = status.last_update.includes('Z') || 
                                   status.last_update.includes('+') || 
                                   (status.last_update.includes('T') && status.last_update.includes('-', status.last_update.indexOf('T')));
                
                // If no timezone info, append 'Z' to treat as UTC
                const utcDateString = hasTimezone ? status.last_update : status.last_update + 'Z';
                
                return format(new Date(utcDateString), 'MMM d, yyyy HH:mm');
              })() : 'Never'}
            </p>
          </div>
          <div className="flex items-center">
            <SeasonSelector 
              selectedSeason={selectedSeason} 
              onSeasonChange={changeSeason}
            />
          </div>
        </div>
        {status?.is_updating && (
          <div className="mt-2 flex items-center text-sm text-blue-600">
            <LoadingSpinner size="small" className="mr-2"/>
            <span>Data update in progress... (Phase: {status.current_phase || 'Initializing'})</span>
          </div>
        )}
      </div>

      {isAnySectionLoading && !status?.is_updating && (
        <div className="text-center p-10">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-lg text-muted-foreground">Loading initial data...</p>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
        {sections.map((section) => (
          <Card key={section.path} className="p-6 shadow-lg hover:shadow-xl transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div className="text-left">
                <h2 className="text-2xl font-semibold text-primary">{section.title}</h2>
                <p className="text-muted-foreground text-sm">{section.description}</p>
              </div>
              {(section.isLoading || (section.isRefetching && section.count === 0)) && !status?.is_updating && <LoadingSpinner size="small" />}
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-4xl font-bold">
                { (section.isRefetching && section.count === 0 && !status?.is_updating) ? '-' : section.count}
              </span>
              <Link
                to={section.path}
                className="text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                View All →
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default HomePage;