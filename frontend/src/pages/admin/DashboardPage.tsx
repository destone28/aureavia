import { useState, useEffect, useCallback } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuthStore } from '../../store/authStore';
import { useRidesStore } from '../../store/ridesStore';
import { useUIStore } from '../../store/uiStore';
import {
  fetchDashboardKPIs,
  fetchEarnings,
  fetchDriversList,
  fetchCompaniesList,
} from '../../services/adminService';
import type {
  DashboardKPIs,
  EarningsDataPoint,
  DriverListItem,
  CompanyListItem,
} from '../../services/adminService';
import type { Ride } from '../../services/ridesService';

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'rides', label: 'Corse' },
  { id: 'drivers', label: 'Driver' },
  { id: 'partners', label: 'Partner' },
] as const;

type TabId = (typeof tabs)[number]['id'];

// --- Status badge helper ---

const statusConfig: Record<string, { label: string; bg: string; text: string }> = {
  to_assign: { label: 'Da Assegnare', bg: 'bg-[#FFF3E0]', text: 'text-[#FF8C00]' },
  booked: { label: 'Prenotata', bg: 'bg-[#E3F2FD]', text: 'text-[#2196F3]' },
  in_progress: { label: 'In Corso', bg: 'bg-[#FFF8E1]', text: 'text-[#FFA000]' },
  completed: { label: 'Completata', bg: 'bg-[#E8F5E9]', text: 'text-[#4CAF50]' },
  cancelled: { label: 'Cancellata', bg: 'bg-[#FFEBEE]', text: 'text-[#F44336]' },
  critical: { label: 'Critica', bg: 'bg-[#FFEBEE]', text: 'text-[#D32F2F]' },
};

function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] ?? { label: status, bg: 'bg-gray-100', text: 'text-gray-600' };
  return (
    <span className={`inline-block px-2.5 py-1 rounded-lg text-xs font-semibold ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
}

// --- Star rating helper ---

function StarRating({ rating }: { rating: number }) {
  const fullStars = Math.floor(rating);
  const hasHalf = rating - fullStars >= 0.25;
  const stars: string[] = [];
  for (let i = 0; i < 5; i++) {
    if (i < fullStars) stars.push('full');
    else if (i === fullStars && hasHalf) stars.push('half');
    else stars.push('empty');
  }
  return (
    <span className="inline-flex items-center gap-0.5">
      {stars.map((type, i) => (
        <svg key={i} className="w-4 h-4" viewBox="0 0 20 20" fill="none">
          {type === 'full' && (
            <path d="M10 1l2.39 4.84 5.34.78-3.87 3.77.91 5.33L10 13.27l-4.77 2.51.91-5.33L2.27 6.68l5.34-.78L10 1z" fill="#FF8C00" />
          )}
          {type === 'half' && (
            <>
              <path d="M10 1l2.39 4.84 5.34.78-3.87 3.77.91 5.33L10 13.27l-4.77 2.51.91-5.33L2.27 6.68l5.34-.78L10 1z" fill="#E0E0E0" />
              <path d="M10 1v12.27l-4.77 2.51.91-5.33L2.27 6.68l5.34-.78L10 1z" fill="#FF8C00" />
            </>
          )}
          {type === 'empty' && (
            <path d="M10 1l2.39 4.84 5.34.78-3.87 3.77.91 5.33L10 13.27l-4.77 2.51.91-5.33L2.27 6.68l5.34-.78L10 1z" fill="#E0E0E0" />
          )}
        </svg>
      ))}
      <span className="ml-1 text-xs text-[#666]">{rating.toFixed(1)}</span>
    </span>
  );
}

// --- Loading spinner ---

function Spinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="w-10 h-10 border-4 border-[#FF8C00] border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

// --- KPI Card ---

function KPICard({ title, value, subtitle, change }: {
  title: string;
  value: string;
  subtitle?: string;
  change?: number;
}) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
      <p className="text-sm text-[#666] mb-1">{title}</p>
      <p className="text-2xl font-bold text-[#2D2D2D]">{value}</p>
      {subtitle && <p className="text-xs text-[#666] mt-1">{subtitle}</p>}
      {change !== undefined && (
        <p className={`text-xs font-semibold mt-2 ${change >= 0 ? 'text-[#4CAF50]' : 'text-[#F44336]'}`}>
          {change >= 0 ? '+' : ''}{change.toFixed(1)}% vs periodo prec.
        </p>
      )}
    </div>
  );
}

// --- Overview Tab ---

function OverviewTab() {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [earningsData, setEarningsData] = useState<EarningsDataPoint[]>([]);
  const [granularity, setGranularity] = useState<string>('daily');
  const [loading, setLoading] = useState(true);
  const addToast = useUIStore((s) => s.addToast);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [kpiResult, earningsResult] = await Promise.all([
        fetchDashboardKPIs(),
        fetchEarnings(granularity),
      ]);
      setKpis(kpiResult);
      setEarningsData(earningsResult.data);
    } catch {
      addToast('error', 'Errore nel caricamento dei dati della dashboard');
    } finally {
      setLoading(false);
    }
  }, [granularity, addToast]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  if (loading) return <Spinner />;

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Corse Totali"
          value={kpis ? kpis.total_rides.toLocaleString('it-IT') : '—'}
          change={kpis?.rides_change_pct}
        />
        <KPICard
          title="Ricavi Totali"
          value={kpis ? `€ ${kpis.total_revenue.toLocaleString('it-IT', { minimumFractionDigits: 2 })}` : '—'}
          change={kpis?.revenue_change_pct}
        />
        <KPICard
          title="Driver Attivi"
          value={kpis ? kpis.active_drivers.toLocaleString('it-IT') : '—'}
        />
        <KPICard
          title="Corse Oggi"
          value={kpis ? kpis.rides_today.toLocaleString('it-IT') : '—'}
        />
      </div>

      {/* Earnings Chart */}
      <div className="bg-white rounded-2xl p-6 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-semibold text-[#2D2D2D]">Andamento Ricavi</h3>
          <div className="flex gap-1 bg-[#F5F5F5] rounded-lg p-1">
            {(['daily', 'weekly', 'monthly'] as const).map((g) => (
              <button
                key={g}
                onClick={() => setGranularity(g)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md border-none cursor-pointer transition-colors ${
                  granularity === g
                    ? 'bg-[#FF8C00] text-white'
                    : 'bg-transparent text-[#666] hover:text-[#2D2D2D]'
                }`}
              >
                {g === 'daily' ? 'Giornaliero' : g === 'weekly' ? 'Settimanale' : 'Mensile'}
              </button>
            ))}
          </div>
        </div>
        {earningsData.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={earningsData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#FF8C00" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#FF8C00" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E0E0E0" />
              <XAxis dataKey="period" tick={{ fontSize: 12, fill: '#666' }} />
              <YAxis tick={{ fontSize: 12, fill: '#666' }} tickFormatter={(v: number) => `€${v}`} />
              <Tooltip
                formatter={(value: number | undefined) => [`€ ${(value ?? 0).toLocaleString('it-IT', { minimumFractionDigits: 2 })}`, 'Ricavi']}
                contentStyle={{ borderRadius: '12px', border: '1px solid #E0E0E0', fontSize: '13px' }}
              />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#FF8C00"
                strokeWidth={2}
                fill="url(#colorRevenue)"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-64 text-[#666] text-sm">
            Nessun dato disponibile per il periodo selezionato
          </div>
        )}
      </div>
    </div>
  );
}

// --- Corse (Rides) Tab ---

function RidesTab() {
  const { rides, isLoading, loadRides } = useRidesStore();

  useEffect(() => {
    void loadRides();
  }, [loadRides]);

  if (isLoading) return <Spinner />;

  return (
    <div className="bg-white rounded-2xl shadow-[0_4px_16px_rgba(0,0,0,0.06)] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-[#E0E0E0]">
              <th className="px-6 py-4 text-xs font-semibold text-[#666] uppercase tracking-wide">ID</th>
              <th className="px-6 py-4 text-xs font-semibold text-[#666] uppercase tracking-wide">Passeggero</th>
              <th className="px-6 py-4 text-xs font-semibold text-[#666] uppercase tracking-wide">Partenza</th>
              <th className="px-6 py-4 text-xs font-semibold text-[#666] uppercase tracking-wide">Arrivo</th>
              <th className="px-6 py-4 text-xs font-semibold text-[#666] uppercase tracking-wide">Data</th>
              <th className="px-6 py-4 text-xs font-semibold text-[#666] uppercase tracking-wide">Stato</th>
              <th className="px-6 py-4 text-xs font-semibold text-[#666] uppercase tracking-wide text-right">Prezzo</th>
            </tr>
          </thead>
          <tbody>
            {rides.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-sm text-[#666]">
                  Nessuna corsa trovata
                </td>
              </tr>
            ) : (
              rides.map((ride: Ride) => (
                <tr
                  key={ride.id}
                  className="border-b border-[#F0F0F0] hover:bg-[#FAFAFA] cursor-pointer transition-colors"
                >
                  <td className="px-6 py-4 text-sm text-[#2D2D2D] font-mono">
                    {ride.external_id ?? ride.id.slice(0, 8)}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2D2D2D]">
                    {ride.passenger_name ?? '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#666] max-w-[200px] truncate">
                    {ride.pickup_address}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#666] max-w-[200px] truncate">
                    {ride.dropoff_address}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#666] whitespace-nowrap">
                    {new Date(ride.scheduled_at).toLocaleDateString('it-IT', {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={ride.status} />
                  </td>
                  <td className="px-6 py-4 text-sm text-[#2D2D2D] font-semibold text-right whitespace-nowrap">
                    {ride.price != null
                      ? `€ ${ride.price.toLocaleString('it-IT', { minimumFractionDigits: 2 })}`
                      : '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- Driver Tab ---

function DriversTab() {
  const [drivers, setDrivers] = useState<DriverListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const addToast = useUIStore((s) => s.addToast);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchDriversList();
        if (!cancelled) setDrivers(data);
      } catch {
        addToast('error', 'Errore nel caricamento dei driver');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [addToast]);

  if (loading) return <Spinner />;

  if (drivers.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-8 shadow-[0_4px_16px_rgba(0,0,0,0.06)] text-center">
        <p className="text-[#666] text-sm">Nessun driver trovato</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {drivers.map((driver) => (
        <div
          key={driver.id}
          className="bg-white rounded-2xl p-5 shadow-[0_4px_16px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_24px_rgba(0,0,0,0.1)] transition-shadow"
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <h4 className="text-sm font-semibold text-[#2D2D2D]">
                {driver.first_name} {driver.last_name}
              </h4>
              <p className="text-xs text-[#666] mt-0.5">{driver.email}</p>
            </div>
            <button className="text-xs text-[#FF8C00] font-medium bg-transparent border-none cursor-pointer hover:underline">
              Modifica
            </button>
          </div>

          <div className="mb-3">
            <StarRating rating={driver.rating_avg} />
          </div>

          <div className="grid grid-cols-2 gap-y-2 text-xs">
            <div>
              <span className="text-[#666]">Targa:</span>{' '}
              <span className="text-[#2D2D2D] font-medium">{driver.vehicle_plate ?? '—'}</span>
            </div>
            <div>
              <span className="text-[#666]">Veicolo:</span>{' '}
              <span className="text-[#2D2D2D] font-medium">
                {driver.vehicle_make && driver.vehicle_model
                  ? `${driver.vehicle_make} ${driver.vehicle_model}`
                  : '—'}
              </span>
            </div>
            <div>
              <span className="text-[#666]">Corse:</span>{' '}
              <span className="text-[#2D2D2D] font-medium">{driver.total_rides}</span>
            </div>
            <div>
              <span className="text-[#666]">Societa:</span>{' '}
              <span className="text-[#2D2D2D] font-medium">{driver.company_name ?? 'Diretto'}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// --- Partner Tab ---

function PartnersTab() {
  const [companies, setCompanies] = useState<CompanyListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const addToast = useUIStore((s) => s.addToast);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchCompaniesList();
        if (!cancelled) setCompanies(data);
      } catch {
        addToast('error', 'Errore nel caricamento dei partner');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [addToast]);

  if (loading) return <Spinner />;

  const companyStatusConfig: Record<string, { label: string; bg: string; text: string }> = {
    active: { label: 'Attivo', bg: 'bg-[#E8F5E9]', text: 'text-[#4CAF50]' },
    inactive: { label: 'Inattivo', bg: 'bg-[#FFEBEE]', text: 'text-[#F44336]' },
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button className="px-5 py-2.5 bg-[#FF8C00] text-white text-sm font-semibold rounded-xl border-none cursor-pointer hover:bg-[#E07B00] transition-colors">
          + Aggiungi Partner
        </button>
      </div>

      {companies.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 shadow-[0_4px_16px_rgba(0,0,0,0.06)] text-center">
          <p className="text-[#666] text-sm">Nessun partner trovato</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {companies.map((company) => {
            const cs = companyStatusConfig[company.status] ?? { label: company.status, bg: 'bg-gray-100', text: 'text-gray-600' };
            return (
              <div
                key={company.id}
                className="bg-white rounded-2xl p-5 shadow-[0_4px_16px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_24px_rgba(0,0,0,0.1)] transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <h4 className="text-sm font-semibold text-[#2D2D2D]">{company.name}</h4>
                  <span className={`inline-block px-2.5 py-1 rounded-lg text-xs font-semibold ${cs.bg} ${cs.text}`}>
                    {cs.label}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  {company.contact_person && (
                    <div>
                      <span className="text-[#666]">Referente:</span>{' '}
                      <span className="text-[#2D2D2D] font-medium">{company.contact_person}</span>
                    </div>
                  )}
                  <div>
                    <span className="text-[#666]">Email:</span>{' '}
                    <span className="text-[#2D2D2D] font-medium">{company.contact_email}</span>
                  </div>
                  {company.contact_phone && (
                    <div>
                      <span className="text-[#666]">Telefono:</span>{' '}
                      <span className="text-[#2D2D2D] font-medium">{company.contact_phone}</span>
                    </div>
                  )}
                  {company.active_drivers !== undefined && (
                    <div>
                      <span className="text-[#666]">Driver attivi:</span>{' '}
                      <span className="text-[#2D2D2D] font-semibold">{company.active_drivers}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// --- Main Dashboard Page ---

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const { logout, user } = useAuthStore();

  return (
    <div className="min-h-screen bg-[#F5F5F5] font-['Open_Sans']">
      {/* Header */}
      <header className="bg-white border-b border-[#E0E0E0] px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#2D2D2D]">
          <span className="text-[#FF8C00]">AureaVia</span> Admin
        </h1>
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm text-[#666]">
              {user.first_name} {user.last_name}
            </span>
          )}
          <button
            onClick={logout}
            className="text-sm text-[#666] hover:text-[#F44336] bg-transparent border-none cursor-pointer transition-colors"
          >
            Esci
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-[#E0E0E0] px-6 flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-3 text-sm font-medium border-none bg-transparent cursor-pointer transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'text-[#FF8C00] border-b-2 border-[#FF8C00] shadow-[inset_0_-2px_0_#FF8C00]'
                : 'text-[#666] hover:text-[#2D2D2D]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="p-6">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'rides' && <RidesTab />}
        {activeTab === 'drivers' && <DriversTab />}
        {activeTab === 'partners' && <PartnersTab />}
      </main>
    </div>
  );
}
