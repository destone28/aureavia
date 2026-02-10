import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Header } from '../../components/common/Header';
import { MobileMenu } from '../../components/common/MobileMenu';
import { ConfirmDialog } from '../../components/common/ConfirmDialog';
import { useRidesStore } from '../../store/ridesStore';
import { useAuthStore } from '../../store/authStore';

const STATUS_LABELS: Record<string, { label: string; bg: string; text: string }> = {
  to_assign: { label: 'Disponibile', bg: 'bg-[#FFF3E0]', text: 'text-[#FF8C00]' },
  critical: { label: 'Urgente', bg: 'bg-[#FFEBEE]', text: 'text-[#F44336]' },
  booked: { label: 'Prenotata', bg: 'bg-[#E8F5E9]', text: 'text-[#4CAF50]' },
  in_progress: { label: 'In corso', bg: 'bg-[#F3E5F5]', text: 'text-[#9C27B0]' },
  completed: { label: 'Completata', bg: 'bg-[#E8F5E9]', text: 'text-[#4CAF50]' },
  cancelled: { label: 'Cancellata', bg: 'bg-[#F5F5F5]', text: 'text-[#9E9E9E]' },
};

function formatDateIT(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('it-IT', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function formatTimeIT(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('it-IT', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

export default function RideDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { currentRide: ride, isLoading, loadRide, acceptRide, startRide, completeRide } = useRidesStore();

  const [menuOpen, setMenuOpen] = useState(false);
  const [showAcceptModal, setShowAcceptModal] = useState(false);
  const [showDeclineDialog, setShowDeclineDialog] = useState(false);
  const [showStartDialog, setShowStartDialog] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (id) loadRide(id);
  }, [id, loadRide]);

  const handleAccept = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await acceptRide(id);
      setShowAcceptModal(true);
    } catch { /* toast handled in store */ }
    setActionLoading(false);
  };

  const handleStart = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await startRide(id);
      setShowStartDialog(false);
    } catch { /* toast handled in store */ }
    setActionLoading(false);
  };

  const handleComplete = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await completeRide(id);
      setShowCompleteDialog(false);
    } catch { /* toast handled in store */ }
    setActionLoading(false);
  };

  const status = ride ? STATUS_LABELS[ride.status] || STATUS_LABELS.to_assign : null;
  const isMyRide = ride?.driver_id === user?.id;
  const canAccept = ride?.status === 'to_assign' || ride?.status === 'critical';
  const canStart = ride?.status === 'booked' && isMyRide;
  const canComplete = ride?.status === 'in_progress' && isMyRide;

  if (isLoading || !ride) {
    return (
      <div className="min-h-screen bg-bg-main">
        <Header onMenuToggle={() => setMenuOpen(true)} />
        <MobileMenu isOpen={menuOpen} onClose={() => setMenuOpen(false)} />
        <div className="pt-16 flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="inline-block w-8 h-8 border-4 border-[#FF8C00] border-t-transparent rounded-full animate-spin" />
            <p className="text-text-secondary text-sm mt-3">Caricamento...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-main pb-28">
      <Header onMenuToggle={() => setMenuOpen(true)} />
      <MobileMenu isOpen={menuOpen} onClose={() => setMenuOpen(false)} />

      <div className="pt-16">
        <div className="max-w-[800px] mx-auto p-4">
          {/* Back button */}
          <button
            onClick={() => navigate('/rides')}
            className="flex items-center gap-2 text-text-secondary text-sm font-semibold mb-4 hover:text-primary transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
            Torna alle corse
          </button>

          {/* Ride ID + Status */}
          <div className="flex items-start justify-between mb-5">
            <div>
              <p className="text-sm text-text-secondary">ID Corsa</p>
              <p className="text-lg font-bold text-text-primary">{ride.id.slice(0, 8).toUpperCase()}</p>
            </div>
            {status && (
              <span className={`px-4 py-1.5 rounded-2xl text-sm font-semibold ${status.bg} ${status.text}`}>
                {status.label}
              </span>
            )}
          </div>

          {/* Route card */}
          <div className="bg-white rounded-xl p-5 mb-3">
            <div className="mb-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-3 h-3 rounded-full bg-[#4CAF50] flex-shrink-0" />
                <span className="text-sm text-text-secondary">Partenza</span>
              </div>
              <p className="text-lg font-semibold text-text-primary ml-6">
                {ride.pickup_address}
              </p>
            </div>

            <div className="ml-1.5 w-0.5 h-6 bg-border" />

            <div className="mt-2">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-3 h-3 rounded-full bg-[#F44336] flex-shrink-0" />
                <span className="text-sm text-text-secondary">Arrivo</span>
              </div>
              <p className="text-lg font-semibold text-text-primary ml-6">
                {ride.dropoff_address}
              </p>
            </div>
          </div>

          {/* Date & Time card */}
          <div className="bg-white rounded-xl p-5 mb-3">
            <div className="flex items-center gap-3 mb-3">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                <line x1="16" y1="2" x2="16" y2="6" />
                <line x1="8" y1="2" x2="8" y2="6" />
                <line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              <span className="text-text-primary">{formatDateIT(ride.scheduled_at)}</span>
            </div>
            <div className="flex items-center gap-3">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
              <span className="text-text-primary">{formatTimeIT(ride.scheduled_at)}</span>
            </div>
          </div>

          {/* Info grid */}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-white rounded-xl p-4">
              <p className="text-xs text-text-secondary mb-1">Passeggeri</p>
              <p className="text-lg font-semibold text-text-primary">{ride.passenger_count}</p>
            </div>
            <div className="bg-white rounded-xl p-4">
              <p className="text-xs text-text-secondary mb-1">Percorso</p>
              <p className="text-lg font-semibold text-text-primary">
                {ride.route_type === 'urban' ? 'Urbano' : 'Extra-urbano'}
              </p>
            </div>
            {ride.distance_km != null && (
              <div className="bg-white rounded-xl p-4">
                <p className="text-xs text-text-secondary mb-1">Distanza</p>
                <p className="text-lg font-semibold text-text-primary">{ride.distance_km} km</p>
              </div>
            )}
            {ride.duration_min != null && (
              <div className="bg-white rounded-xl p-4">
                <p className="text-xs text-text-secondary mb-1">Durata stimata</p>
                <p className="text-lg font-semibold text-text-primary">{ride.duration_min} min</p>
              </div>
            )}
          </div>

          {/* Passenger info */}
          {ride.passenger_name && (
            <div className="bg-white rounded-xl p-5 mb-3">
              <div className="flex items-center gap-3 mb-3">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                <span className="text-text-primary font-medium">{ride.passenger_name}</span>
              </div>
              {ride.passenger_phone && (
                <div className="flex items-center gap-3">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                  </svg>
                  <a href={`tel:${ride.passenger_phone}`} className="text-primary font-medium">
                    {ride.passenger_phone}
                  </a>
                </div>
              )}
            </div>
          )}

          {/* Notes */}
          {ride.notes && (
            <div className="bg-[#FFFBF0] border-l-4 border-[#FFC107] rounded-xl p-4 mb-3">
              <p className="font-bold text-text-primary text-sm mb-1">Note speciali</p>
              <p className="text-text-secondary text-sm leading-relaxed">{ride.notes}</p>
            </div>
          )}

          {/* Earnings */}
          {ride.driver_share != null && (
            <div className="bg-[#F0F9FF] border-l-4 border-[#FF8C00] rounded-xl p-4 mb-3 flex items-center justify-between">
              <span className="text-text-primary font-medium">Il tuo guadagno</span>
              <span className="text-[28px] font-bold text-primary">&euro;{ride.driver_share.toFixed(2)}</span>
            </div>
          )}

          {/* Map button */}
          {ride.pickup_lat && ride.pickup_lng && (
            <a
              href={`https://maps.google.com/?q=${ride.pickup_lat},${ride.pickup_lng}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-3 w-full bg-white border-2 border-[#FF8C00] rounded-xl p-4 mb-3 hover:bg-[#FFF5E6] hover:-translate-y-0.5 hover:shadow-md transition-all"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF8C00" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                <circle cx="12" cy="10" r="3" />
              </svg>
              <span className="text-[#FF8C00] font-semibold">Naviga al punto di ritiro</span>
            </a>
          )}
        </div>
      </div>

      {/* Bottom action bar */}
      {(canAccept || canStart || canComplete) && (
        <div className="fixed bottom-0 left-0 right-0 bg-white shadow-[0_-2px_8px_rgba(0,0,0,0.1)] p-4">
          <div className="max-w-[800px] mx-auto flex gap-3">
            {canAccept && (
              <>
                <button
                  onClick={() => setShowDeclineDialog(true)}
                  className="flex-1 py-4 rounded-xl border-2 border-border text-text-secondary font-semibold transition-colors hover:border-[#ccc]"
                >
                  Rifiuta
                </button>
                <button
                  onClick={handleAccept}
                  disabled={actionLoading}
                  className="flex-1 py-4 rounded-xl bg-[#FF8C00] text-white font-semibold transition-colors hover:bg-[#E67E00] disabled:opacity-50"
                >
                  {actionLoading ? 'Accettando...' : 'Accetta'}
                </button>
              </>
            )}
            {canStart && (
              <button
                onClick={() => setShowStartDialog(true)}
                disabled={actionLoading}
                className="flex-1 py-4 rounded-xl bg-[#FF8C00] text-white font-semibold transition-colors hover:bg-[#E67E00] disabled:opacity-50"
              >
                Avvia corsa
              </button>
            )}
            {canComplete && (
              <button
                onClick={() => setShowCompleteDialog(true)}
                disabled={actionLoading}
                className="flex-1 py-4 rounded-xl bg-[#4CAF50] text-white font-semibold transition-colors hover:bg-[#43A047] disabled:opacity-50"
              >
                Completa corsa
              </button>
            )}
          </div>
        </div>
      )}

      {/* Assigned message for other drivers */}
      {ride.status === 'booked' && !isMyRide && (
        <div className="fixed bottom-0 left-0 right-0 bg-[#E3F2FD] border-t-4 border-[#2196F3] p-5 text-center">
          <p className="text-lg font-bold text-text-primary">Corsa già assegnata</p>
          <p className="text-sm text-text-secondary mt-1">Questa corsa è stata assegnata ad un altro driver.</p>
        </div>
      )}

      {/* Accept success modal */}
      {showAcceptModal && (
        <div className="fixed inset-0 bg-black/50 z-[1000] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-[400px] w-full text-center">
            <div className="w-20 h-20 rounded-full bg-[#4CAF50] mx-auto flex items-center justify-center animate-[scaleIn_0.3s_ease-out]">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-text-primary mt-6">Corsa accettata!</h3>
            <p className="text-text-secondary mt-2">Sei stato assegnato alla corsa.</p>

            <div className="bg-bg-main rounded-xl p-4 mt-6 text-left space-y-2">
              <p className="text-sm text-text-secondary">
                <strong className="text-text-primary">Data:</strong> {formatDateIT(ride.scheduled_at)}
              </p>
              <p className="text-sm text-text-secondary">
                <strong className="text-text-primary">Ora:</strong> {formatTimeIT(ride.scheduled_at)}
              </p>
              <p className="text-sm text-text-secondary">
                <strong className="text-text-primary">Partenza:</strong> {ride.pickup_address}
              </p>
            </div>

            {ride.pickup_lat && ride.pickup_lng && (
              <a
                href={`https://maps.google.com/?q=${ride.pickup_lat},${ride.pickup_lng}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full py-4 rounded-xl bg-[#FF8C00] text-white font-semibold mt-6 hover:bg-[#E67E00] transition-colors text-center"
              >
                Naviga al ritiro
              </a>
            )}

            {ride.passenger_phone && (
              <a
                href={`tel:${ride.passenger_phone}`}
                className="block w-full py-4 rounded-xl border-2 border-border text-text-secondary font-semibold mt-3 hover:border-[#ccc] transition-colors text-center"
              >
                Chiama passeggero
              </a>
            )}

            <button
              onClick={() => {
                setShowAcceptModal(false);
                navigate('/rides');
              }}
              className="w-full py-3 text-text-secondary font-medium mt-4 hover:text-primary transition-colors"
            >
              Chiudi
            </button>
          </div>
        </div>
      )}

      {/* Decline dialog */}
      <ConfirmDialog
        isOpen={showDeclineDialog}
        title="Rifiuta corsa"
        message="Sei sicuro di voler rifiutare questa corsa? L'azione non è reversibile."
        confirmLabel="Rifiuta"
        cancelLabel="Annulla"
        variant="danger"
        onConfirm={() => {
          setShowDeclineDialog(false);
          navigate('/rides');
        }}
        onCancel={() => setShowDeclineDialog(false)}
      />

      {/* Start dialog */}
      <ConfirmDialog
        isOpen={showStartDialog}
        title="Avvia corsa"
        message="Confermi di voler avviare questa corsa? Il passeggero verrà notificato."
        confirmLabel="Avvia"
        cancelLabel="Annulla"
        onConfirm={handleStart}
        onCancel={() => setShowStartDialog(false)}
      />

      {/* Complete dialog */}
      <ConfirmDialog
        isOpen={showCompleteDialog}
        title="Completa corsa"
        message="Confermi di aver completato la corsa? Il passeggero è arrivato a destinazione?"
        confirmLabel="Completa"
        cancelLabel="Annulla"
        onConfirm={handleComplete}
        onCancel={() => setShowCompleteDialog(false)}
      />
    </div>
  );
}
