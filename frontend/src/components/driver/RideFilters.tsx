import { useState } from 'react';

interface RideFiltersProps {
  activeTab: 'all' | 'available' | 'assigned';
  onTabChange: (tab: 'all' | 'available' | 'assigned') => void;
  filters: {
    passengers: string[];
    route: string[];
    distance: string[];
  };
  onFilterChange: (type: string, value: string) => void;
  onClearFilters: () => void;
  totalCount: number;
}

const TABS: { key: 'all' | 'available' | 'assigned'; label: string }[] = [
  { key: 'all', label: 'Tutte' },
  { key: 'available', label: 'Disponibili' },
  { key: 'assigned', label: 'Assegnate' },
];

const FILTER_GROUPS = [
  {
    key: 'passengers',
    label: 'Passeggeri',
    options: ['1-2', '3-4', '5+'],
  },
  {
    key: 'route',
    label: 'Tipo percorso',
    options: ['Urbano', 'Extra-urbano'],
  },
  {
    key: 'distance',
    label: 'Distanza',
    options: ['<20 km', '20-50 km', '>50 km'],
  },
];

export function RideFilters({
  activeTab,
  onTabChange,
  filters,
  onFilterChange,
  onClearFilters,
  totalCount,
}: RideFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const activeFilterCount =
    filters.passengers.length + filters.route.length + filters.distance.length;

  const isChipActive = (type: string, value: string): boolean => {
    const group = filters[type as keyof typeof filters];
    return Array.isArray(group) && group.includes(value);
  };

  return (
    <div>
      {/* Navigation Tabs */}
      <div className="flex border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => onTabChange(tab.key)}
            className={`flex-1 py-3 text-sm font-semibold text-center transition-colors relative ${
              activeTab === tab.key
                ? 'text-[#FF8C00]'
                : 'text-[#666666] hover:text-[#2D2D2D]'
            }`}
          >
            {tab.label}
            {activeTab === tab.key && (
              <span className="absolute bottom-0 left-0 right-0 h-[3px] bg-[#FF8C00] rounded-t-full" />
            )}
          </button>
        ))}
      </div>

      {/* Collapsible Filter Section */}
      <div className="bg-white">
        {/* Filter header */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between px-4 py-3"
        >
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-[#2D2D2D]">Filtri</span>
            {activeFilterCount > 0 && (
              <span className="w-5 h-5 rounded-full bg-[#FF8C00] text-white text-xs font-bold flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#666666]">
              {totalCount} cors{totalCount === 1 ? 'a' : 'e'}
            </span>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className={`text-[#666666] transition-transform duration-200 ${
                isExpanded ? 'rotate-180' : ''
              }`}
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </div>
        </button>

        {/* Filter content */}
        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out ${
            isExpanded ? 'max-h-[400px] opacity-100' : 'max-h-0 opacity-0'
          }`}
        >
          <div className="px-4 pb-4">
            {/* Reset button */}
            {activeFilterCount > 0 && (
              <button
                onClick={onClearFilters}
                className="text-xs text-[#FF8C00] font-semibold mb-3 hover:underline"
              >
                Reset filtri
              </button>
            )}

            {/* Filter groups */}
            {FILTER_GROUPS.map((group) => (
              <div key={group.key} className="mb-3 last:mb-0">
                <p className="text-xs text-[#666666] font-medium mb-2">
                  {group.label}
                </p>
                <div className="flex flex-wrap gap-2">
                  {group.options.map((option) => {
                    const active = isChipActive(group.key, option);
                    return (
                      <button
                        key={option}
                        onClick={() => onFilterChange(group.key, option)}
                        className={`rounded-full border text-sm font-medium transition-all ${
                          active
                            ? 'bg-gradient-to-r from-[#FF8C00] to-[#FFA500] text-white border-transparent shadow-sm'
                            : 'bg-white text-[#2D2D2D] border-gray-200 hover:border-[#FF8C00]'
                        }`}
                        style={{ padding: '10px 18px' }}
                      >
                        {option}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
