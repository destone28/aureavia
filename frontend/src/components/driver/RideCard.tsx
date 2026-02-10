import type { Ride } from '../../services/ridesService';

interface RideCardProps {
  ride: Ride;
  onClick: (id: string) => void;
}

const STATUS_MAP: Record<
  Ride['status'],
  { label: string; bg: string; text: string }
> = {
  to_assign: { label: 'Disponibile', bg: 'bg-[#FFF3E0]', text: 'text-[#FF8C00]' },
  critical: { label: 'Disponibile', bg: 'bg-[#FFF3E0]', text: 'text-[#FF8C00]' },
  booked: { label: 'Assegnata', bg: 'bg-[#E8F5E9]', text: 'text-[#4CAF50]' },
  in_progress: { label: 'In corso', bg: 'bg-[#F3E5F5]', text: 'text-[#9C27B0]' },
  completed: { label: 'Completata', bg: 'bg-[#E8F5E9]', text: 'text-[#4CAF50]' },
  cancelled: { label: 'Cancellata', bg: 'bg-[#F5F5F5]', text: 'text-[#9E9E9E]' },
};

function getSourceBadge(source: string): { label: string; color: string } {
  if (source === 'booking.com') {
    return { label: 'Booking.com', color: '#003580' };
  }
  if (source === 'manual') {
    return { label: 'Manuale', color: '#424242' };
  }
  return { label: source, color: '#424242' };
}

function formatDateIT(dateStr: string): string {
  const date = new Date(dateStr);
  const months = [
    'Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu',
    'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic',
  ];
  const day = date.getDate();
  const month = months[date.getMonth()];
  const year = date.getFullYear();
  return `${day} ${month} ${year}`;
}

function formatTimeIT(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

export function RideCard({ ride, onClick }: RideCardProps) {
  const status = STATUS_MAP[ride.status] || STATUS_MAP.to_assign;
  const source = getSourceBadge(ride.source_platform);
  const routeLabel =
    ride.route_type === 'urban' ? 'Urbano' : 'Extra-urbano';

  return (
    <div
      onClick={() => onClick(ride.id)}
      className="bg-white rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
    >
      {/* Header: Status + Source badges */}
      <div className="flex items-center gap-2 mb-3">
        <span
          className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${status.bg} ${status.text}`}
        >
          {status.label}
        </span>
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold text-white" style={{ backgroundColor: source.color }}>
          {source.label}
        </span>
      </div>

      {/* DateTime row */}
      <div className="flex items-center gap-4 mb-3 text-[#666666] text-sm">
        <div className="flex items-center gap-1.5">
          {/* Calendar icon */}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#999]">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <span>{formatDateIT(ride.scheduled_at)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          {/* Clock icon */}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#999]">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span>{formatTimeIT(ride.scheduled_at)}</span>
        </div>
      </div>

      {/* Route section */}
      <div className="mb-3 space-y-2">
        <div className="flex items-start gap-2.5">
          <div className="w-2 h-2 rounded-full bg-[#4CAF50] mt-1.5 flex-shrink-0" />
          <span className="text-[#2D2D2D] text-sm leading-tight">
            {ride.pickup_address}
          </span>
        </div>
        <div className="flex items-start gap-2.5">
          <div className="w-2 h-2 rounded-full bg-[#F44336] mt-1.5 flex-shrink-0" />
          <span className="text-[#2D2D2D] text-sm leading-tight">
            {ride.dropoff_address}
          </span>
        </div>
      </div>

      {/* Info badges */}
      <div className="flex items-center gap-2 mb-4">
        {/* Passenger count */}
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#F5F5F5] text-[#666666] text-xs">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          {ride.passenger_count}
        </span>
        {/* Route type */}
        {ride.route_type && (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#F5F5F5] text-[#666666] text-xs">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            </svg>
            {routeLabel}
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-100 pt-3 flex items-center justify-between">
        <div className="flex items-center gap-3 text-[#666666] text-xs">
          {ride.distance_km != null && (
            <span>{ride.distance_km} km</span>
          )}
        </div>
        <div className="flex items-center gap-4">
          {ride.price != null && (
            <span className="text-[#FF8C00] font-bold text-xl">
              &euro;{ride.price.toFixed(2)}
            </span>
          )}
          <span className="text-[#FF8C00] text-sm font-semibold">
            Dettagli &rarr;
          </span>
        </div>
      </div>
    </div>
  );
}
