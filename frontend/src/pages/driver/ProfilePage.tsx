import { useEffect, useState } from 'react';
import { Header } from '../../components/common/Header';
import { MobileMenu } from '../../components/common/MobileMenu';
import { useAuthStore } from '../../store/authStore';
import { fetchMyDriver, fetchDriverStats } from '../../services/driverService';
import type { DriverProfile, DriverStats } from '../../services/driverService';

type Tab = 'profilo' | 'veicolo' | 'attivita';

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return '—';
  }
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('it-IT', {
    style: 'currency',
    currency: 'EUR',
  }).format(value);
}

function formatKm(value: number): string {
  return new Intl.NumberFormat('it-IT', { maximumFractionDigits: 0 }).format(value) + ' km';
}

/* ── Icon components ── */

function UserIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function MailIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  );
}

function PhoneIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
  );
}

function IdCardIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <circle cx="8" cy="11" r="2" />
      <path d="M4 18s1-2 4-2 4 2 4 2" />
      <line x1="15" y1="9" x2="20" y2="9" />
      <line x1="15" y1="13" x2="20" y2="13" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}

function AwardIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="6" />
      <path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11" />
    </svg>
  );
}

function CarIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9L18 10l-2.7-3.6A2 2 0 0 0 13.7 5H6.3a2 2 0 0 0-1.6.9L2 9.5.5 11.1c-.3.2-.5.6-.5 1V16c0 .6.4 1 1 1h2" />
      <circle cx="7" cy="17" r="2" />
      <circle cx="17" cy="17" r="2" />
    </svg>
  );
}

function CalendarIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}

function UsersIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function BriefcaseIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
    </svg>
  );
}

function FuelIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 22V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v17" />
      <path d="M15 10h2a2 2 0 0 1 2 2v2a2 2 0 0 0 2 2h0a2 2 0 0 0 2-2V9.83a2 2 0 0 0-.59-1.42L18 4" />
      <path d="M6 12h6" />
    </svg>
  );
}

function StarIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="#FF8C00" stroke="#FF8C00" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  );
}

function TrendingUpIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
      <polyline points="16 7 22 7 22 13" />
    </svg>
  );
}

function MapPinIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  );
}

function EuroIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 10h12" />
      <path d="M4 14h9" />
      <path d="M19 6a7.7 7.7 0 0 0-5.2-2A7.9 7.9 0 0 0 6 12a7.9 7.9 0 0 0 7.8 8 7.7 7.7 0 0 0 5.2-2" />
    </svg>
  );
}

/* ── Reusable row component ── */

interface InfoRowProps {
  icon: React.ReactNode;
  label: string;
  value: string;
}

function InfoRow({ icon, label, value }: InfoRowProps) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-gray-100 last:border-b-0">
      <span className="text-[#FF8C00] mt-0.5 flex-shrink-0">{icon}</span>
      <div className="min-w-0 flex-1">
        <p className="text-xs text-[#666666] mb-0.5">{label}</p>
        <p className="text-sm font-medium text-[#2D2D2D] break-words">{value}</p>
      </div>
    </div>
  );
}

/* ── Stat card component ── */

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent?: boolean;
}

function StatCard({ icon, label, value, accent }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className={accent ? 'text-[#FF8C00]' : 'text-[#666666]'}>{icon}</span>
        <span className="text-xs text-[#666666]">{label}</span>
      </div>
      <p className={`text-lg font-bold ${accent ? 'text-[#FF8C00]' : 'text-[#2D2D2D]'}`}>
        {value}
      </p>
    </div>
  );
}

/* ── Main page ── */

export default function ProfilePage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('profilo');
  const [driver, setDriver] = useState<DriverProfile | null>(null);
  const [stats, setStats] = useState<DriverStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const user = useAuthStore((s) => s.user);

  const initials = user
    ? `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase()
    : 'AV';
  const fullName = user ? `${user.first_name} ${user.last_name}` : '';

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const driverData = await fetchMyDriver();
        if (cancelled) return;
        setDriver(driverData);

        if (driverData?.id) {
          const statsData = await fetchDriverStats(driverData.id);
          if (cancelled) return;
          setStats(statsData);
        }
      } catch (err: any) {
        if (cancelled) return;
        setError(err.response?.data?.detail || 'Errore nel caricamento del profilo');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  const tabs: { key: Tab; label: string }[] = [
    { key: 'profilo', label: 'Profilo' },
    { key: 'veicolo', label: 'Veicolo' },
    { key: 'attivita', label: 'Attivit\u00e0' },
  ];

  const roleBadgeLabel = (() => {
    if (!user) return '';
    switch (user.role) {
      case 'admin': return 'Amministratore';
      case 'assistant': return 'Assistente';
      case 'finance': return 'Operatore Finanziario';
      case 'driver': return 'Driver';
      default: return user.role;
    }
  })();

  /* ── Render helpers ── */

  function renderProfiloTab() {
    if (!driver) return null;

    const permits = driver.special_permits;
    let permitsStr = '—';
    if (permits) {
      if (Array.isArray(permits)) {
        permitsStr = permits.length > 0 ? permits.join(', ') : '—';
      } else if (typeof permits === 'string') {
        permitsStr = permits || '—';
      } else if (typeof permits === 'object') {
        const keys = Object.keys(permits);
        permitsStr = keys.length > 0 ? keys.join(', ') : '—';
      }
    }

    return (
      <div className="space-y-4">
        {/* Personal info */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h3 className="text-sm font-semibold text-[#2D2D2D] mb-1">Dati personali</h3>
          <InfoRow icon={<UserIcon />} label="Nome completo" value={fullName || '—'} />
          <InfoRow icon={<MailIcon />} label="Email" value={user?.email || '—'} />
          <InfoRow icon={<PhoneIcon />} label="Telefono" value={user?.phone || '—'} />
        </div>

        {/* License */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h3 className="text-sm font-semibold text-[#2D2D2D] mb-1">Patente</h3>
          <InfoRow icon={<IdCardIcon />} label="Numero patente" value={driver.license_number || '—'} />
          <InfoRow icon={<CalendarIcon />} label="Scadenza patente" value={formatDate(driver.license_expiry)} />
        </div>

        {/* Insurance */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h3 className="text-sm font-semibold text-[#2D2D2D] mb-1">Assicurazione</h3>
          <InfoRow icon={<ShieldIcon />} label="Numero polizza" value={driver.insurance_number || '—'} />
          <InfoRow icon={<CalendarIcon />} label="Scadenza polizza" value={formatDate(driver.insurance_expiry)} />
        </div>

        {/* Special permits */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h3 className="text-sm font-semibold text-[#2D2D2D] mb-1">Permessi speciali</h3>
          <InfoRow icon={<AwardIcon />} label="Permessi" value={permitsStr} />
        </div>
      </div>
    );
  }

  function renderVeicoloTab() {
    if (!driver) return null;

    return (
      <div className="space-y-4">
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h3 className="text-sm font-semibold text-[#2D2D2D] mb-1">Informazioni veicolo</h3>
          <InfoRow
            icon={<CarIcon />}
            label="Marca e Modello"
            value={
              driver.vehicle_make || driver.vehicle_model
                ? `${driver.vehicle_make || ''} ${driver.vehicle_model || ''}`.trim()
                : '—'
            }
          />
          <InfoRow icon={<IdCardIcon />} label="Targa" value={driver.vehicle_plate || '—'} />
          <InfoRow icon={<CalendarIcon />} label="Anno" value={driver.vehicle_year ? String(driver.vehicle_year) : '—'} />
          <InfoRow icon={<UsersIcon />} label="Posti" value={String(driver.vehicle_seats)} />
          <InfoRow icon={<BriefcaseIcon />} label="Capacit\u00e0 bagagli" value={String(driver.vehicle_luggage_capacity)} />
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4">
          <h3 className="text-sm font-semibold text-[#2D2D2D] mb-1">Dettagli tecnici</h3>
          <InfoRow icon={<FuelIcon />} label="Tipo carburante" value={driver.vehicle_fuel_type || '—'} />
          <InfoRow icon={<CalendarIcon />} label="Data revisione" value={formatDate(driver.vehicle_inspection_date)} />
        </div>
      </div>
    );
  }

  function renderAttivitaTab() {
    const s = stats;
    const d = driver;

    return (
      <div className="space-y-4">
        {/* Main stats */}
        <div className="grid grid-cols-2 gap-3">
          <StatCard
            icon={<CarIcon />}
            label="Corse totali"
            value={String(s?.total_rides ?? d?.total_rides ?? 0)}
          />
          <StatCard
            icon={<MapPinIcon />}
            label="Km totali"
            value={formatKm(s?.total_km ?? d?.total_km ?? 0)}
          />
          <StatCard
            icon={<EuroIcon />}
            label="Guadagno totale"
            value={formatCurrency(s?.total_earnings ?? d?.total_earnings ?? 0)}
            accent
          />
          <StatCard
            icon={<StarIcon />}
            label="Rating medio"
            value={`${(s?.rating_avg ?? d?.rating_avg ?? 0).toFixed(1)} / 5`}
            accent
          />
        </div>

        {/* This month */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h3 className="text-sm font-semibold text-[#2D2D2D] mb-3">Questo mese</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-[#FFF5E6] rounded-lg p-3 text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <TrendingUpIcon />
              </div>
              <p className="text-lg font-bold text-[#FF8C00]">{s?.completed_this_month ?? 0}</p>
              <p className="text-xs text-[#666666]">Corse</p>
            </div>
            <div className="bg-[#FFF5E6] rounded-lg p-3 text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <EuroIcon />
              </div>
              <p className="text-lg font-bold text-[#FF8C00]">{formatCurrency(s?.earnings_this_month ?? 0)}</p>
              <p className="text-xs text-[#666666]">Guadagno</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-main">
      <Header onMenuToggle={() => setMenuOpen(true)} />
      <MobileMenu isOpen={menuOpen} onClose={() => setMenuOpen(false)} />

      {/* Spacer for fixed header */}
      <div className="pt-16">
        <div className="max-w-[800px] mx-auto p-4 space-y-4">

          {/* ── Profile card ── */}
          <div className="bg-white rounded-xl shadow-sm p-6 flex flex-col items-center text-center">
            {/* Avatar */}
            <div className="w-20 h-20 rounded-full bg-[#FF8C00] flex items-center justify-center mb-3">
              <span className="text-white font-bold text-2xl">{initials}</span>
            </div>
            {/* Name */}
            <h2 className="text-lg font-bold text-[#2D2D2D]">{fullName}</h2>
            {/* Email */}
            <p className="text-sm text-[#666666] mt-0.5">{user?.email}</p>
            {/* Role badge */}
            <span className="mt-2 inline-block bg-[#FFF5E6] text-[#FF8C00] text-xs font-semibold px-3 py-1 rounded-full">
              {roleBadgeLabel}
            </span>
          </div>

          {/* ── Tab navigation ── */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="flex border-b border-gray-100">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex-1 py-3 text-sm font-semibold transition-colors relative ${
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
          </div>

          {/* ── Tab content ── */}
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block w-8 h-8 border-4 border-[#FF8C00] border-t-transparent rounded-full animate-spin" />
              <p className="text-[#666666] text-sm mt-3">Caricamento profilo...</p>
            </div>
          ) : error ? (
            <div className="bg-white rounded-xl shadow-sm p-8 text-center">
              <div className="text-4xl mb-3">&#9888;&#65039;</div>
              <h3 className="text-base font-semibold text-[#2D2D2D] mb-1">Errore</h3>
              <p className="text-sm text-[#666666]">{error}</p>
            </div>
          ) : (
            <>
              {activeTab === 'profilo' && renderProfiloTab()}
              {activeTab === 'veicolo' && renderVeicoloTab()}
              {activeTab === 'attivita' && renderAttivitaTab()}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
