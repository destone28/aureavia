import { useEffect, useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '../../components/common/Header';
import { MobileMenu } from '../../components/common/MobileMenu';
import { RideCard } from '../../components/driver/RideCard';
import { RideFilters } from '../../components/driver/RideFilters';
import { useRidesStore } from '../../store/ridesStore';
import type { Ride } from '../../services/ridesService';

type Tab = 'all' | 'available' | 'assigned';

interface LocalFilters {
  passengers: string[];
  route: string[];
  distance: string[];
}

function matchesPassengerFilter(ride: Ride, filters: string[]): boolean {
  if (filters.length === 0) return true;
  const count = ride.passenger_count;
  return filters.some((f) => {
    if (f === '1-2') return count >= 1 && count <= 2;
    if (f === '3-4') return count >= 3 && count <= 4;
    if (f === '5+') return count >= 5;
    return false;
  });
}

function matchesRouteFilter(ride: Ride, filters: string[]): boolean {
  if (filters.length === 0) return true;
  return filters.some((f) => {
    if (f === 'Urbano') return ride.route_type === 'urban';
    if (f === 'Extra-urbano') return ride.route_type === 'extra_urban';
    return false;
  });
}

function matchesDistanceFilter(ride: Ride, filters: string[]): boolean {
  if (filters.length === 0) return true;
  const km = ride.distance_km ?? 0;
  return filters.some((f) => {
    if (f === '<20 km') return km < 20;
    if (f === '20-50 km') return km >= 20 && km <= 50;
    if (f === '>50 km') return km > 50;
    return false;
  });
}

export default function RidesListPage() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('all');
  const [localFilters, setLocalFilters] = useState<LocalFilters>({
    passengers: [],
    route: [],
    distance: [],
  });

  const { rides, isLoading, loadRides } = useRidesStore();

  useEffect(() => {
    loadRides();
  }, [loadRides]);

  const handleTabChange = useCallback((tab: Tab) => {
    setActiveTab(tab);
  }, []);

  const handleFilterChange = useCallback((type: string, value: string) => {
    setLocalFilters((prev) => {
      const key = type as keyof LocalFilters;
      const current = prev[key];
      const updated = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value];
      return { ...prev, [key]: updated };
    });
  }, []);

  const handleClearFilters = useCallback(() => {
    setLocalFilters({ passengers: [], route: [], distance: [] });
  }, []);

  const filteredRides = useMemo(() => {
    return rides.filter((ride) => {
      // Tab filter
      if (activeTab === 'available' && ride.status !== 'to_assign' && ride.status !== 'critical') return false;
      if (activeTab === 'assigned' && ride.status !== 'booked' && ride.status !== 'in_progress') return false;

      // Local filters
      if (!matchesPassengerFilter(ride, localFilters.passengers)) return false;
      if (!matchesRouteFilter(ride, localFilters.route)) return false;
      if (!matchesDistanceFilter(ride, localFilters.distance)) return false;

      return true;
    });
  }, [rides, activeTab, localFilters]);

  return (
    <div className="min-h-screen bg-bg-main">
      <Header onMenuToggle={() => setMenuOpen(true)} />
      <MobileMenu isOpen={menuOpen} onClose={() => setMenuOpen(false)} />

      {/* Spacer for fixed header */}
      <div className="pt-16">
        {/* Filters */}
        <div className="max-w-[800px] mx-auto">
          <div className="bg-white rounded-2xl shadow-sm overflow-hidden mx-4 mt-4">
            <RideFilters
              activeTab={activeTab}
              onTabChange={handleTabChange}
              filters={localFilters}
              onFilterChange={handleFilterChange}
              onClearFilters={handleClearFilters}
              totalCount={filteredRides.length}
            />
          </div>
        </div>

        {/* Rides list */}
        <div className="max-w-[800px] mx-auto p-4 space-y-3">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block w-8 h-8 border-4 border-[#FF8C00] border-t-transparent rounded-full animate-spin" />
              <p className="text-text-secondary text-sm mt-3">Caricamento corse...</p>
            </div>
          ) : filteredRides.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 shadow-sm text-center">
              <div className="text-5xl mb-4">🚗</div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">Nessuna corsa</h3>
              <p className="text-text-secondary text-sm">
                Non ci sono corse che corrispondono ai filtri selezionati.
              </p>
            </div>
          ) : (
            filteredRides.map((ride) => (
              <RideCard
                key={ride.id}
                ride={ride}
                onClick={(id) => navigate(`/rides/${id}`)}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
