import { useState, useEffect } from 'react';
import { assignRide, cancelRide } from '../../services/ridesService';
import { fetchDriversList } from '../../services/adminService';
import type { Ride } from '../../services/ridesService';
import type { DriverListItem } from '../../services/adminService';

const statusConfig: Record<string, { label: string; bg: string; text: string }> = {
  to_assign: { label: 'Da Assegnare', bg: 'bg-[#FFF3E0]', text: 'text-[#FF8C00]' },
  booked: { label: 'Prenotata', bg: 'bg-[#E3F2FD]', text: 'text-[#2196F3]' },
  in_progress: { label: 'In Corso', bg: 'bg-[#FFF8E1]', text: 'text-[#FFA000]' },
  completed: { label: 'Completata', bg: 'bg-[#E8F5E9]', text: 'text-[#4CAF50]' },
  cancelled: { label: 'Cancellata', bg: 'bg-[#FFEBEE]', text: 'text-[#F44336]' },
  critical: { label: 'Critica', bg: 'bg-[#FFEBEE]', text: 'text-[#D32F2F]' },
};

interface Props {
  ride: Ride;
  onClose: () => void;
  onUpdate: (ride: Ride) => void;
}

export default function RideDetailModal({ ride, onClose, onUpdate }: Props) {
  const [drivers, setDrivers] = useState<DriverListItem[]>([]);
  const [selectedDriverId, setSelectedDriverId] = useState('');
  const [isAssigning, setIsAssigning] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [cancelNotes, setCancelNotes] = useState('');
  const [error, setError] = useState('');

  const config = statusConfig[ride.status] ?? { label: ride.status, bg: 'bg-gray-100', text: 'text-gray-600' };
  const canAssign = ride.status === 'to_assign' || ride.status === 'critical';
  const canCancel = !['completed', 'cancelled'].includes(ride.status);

  useEffect(() => {
    if (canAssign) {
      fetchDriversList().then(setDrivers).catch(() => {});
    }
  }, [canAssign]);

  const handleAssign = async () => {
    if (!selectedDriverId) return;
    setIsAssigning(true);
    setError('');
    try {
      const updated = await assignRide(ride.id, selectedDriverId);
      onUpdate(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore nell\'assegnazione');
    } finally {
      setIsAssigning(false);
    }
  };

  const handleCancel = async () => {
    setIsCancelling(true);
    setError('');
    try {
      const updated = await cancelRide(ride.id, cancelNotes || undefined);
      onUpdate(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore nella cancellazione');
    } finally {
      setIsCancelling(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#E0E0E0]">
          <div>
            <h2 className="text-lg font-semibold text-[#2D2D2D]">Dettaglio Corsa</h2>
            <p className="text-xs text-[#666] mt-0.5 font-mono">
              {ride.external_id ?? ride.id.slice(0, 8)}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className={`inline-block px-2.5 py-1 rounded-lg text-xs font-semibold ${config.bg} ${config.text}`}>
              {config.label}
            </span>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#F5F5F5] text-[#666] border-none cursor-pointer hover:bg-[#E0E0E0] transition-colors"
            >
              &times;
            </button>
          </div>
        </div>

        {/* Info Grid */}
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <InfoItem label="Passeggero" value={ride.passenger_name ?? '—'} />
            <InfoItem label="Telefono" value={ride.passenger_phone ?? '—'} />
            <InfoItem label="Partenza" value={ride.pickup_address} full />
            <InfoItem label="Arrivo" value={ride.dropoff_address} full />
            <InfoItem
              label="Data/Ora"
              value={new Date(ride.scheduled_at).toLocaleDateString('it-IT', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit',
              })}
            />
            <InfoItem
              label="Prezzo"
              value={ride.price != null ? `€ ${ride.price.toLocaleString('it-IT', { minimumFractionDigits: 2 })}` : '—'}
            />
            <InfoItem label="Passeggeri" value={String(ride.passenger_count)} />
            <InfoItem label="Piattaforma" value={ride.source_platform} />
            {ride.distance_km != null && (
              <InfoItem label="Distanza" value={`${ride.distance_km} km`} />
            )}
            {ride.duration_min != null && (
              <InfoItem label="Durata" value={`${ride.duration_min} min`} />
            )}
            {ride.flight_number && (
              <InfoItem label="Volo" value={ride.flight_number} />
            )}
            {ride.booking_reference && (
              <InfoItem label="Rif. Prenotazione" value={ride.booking_reference} />
            )}
          </div>

          {ride.notes && (
            <div className="bg-[#F5F5F5] rounded-xl p-3">
              <p className="text-xs text-[#666] mb-1">Note</p>
              <p className="text-sm text-[#2D2D2D]">{ride.notes}</p>
            </div>
          )}

          {error && (
            <div className="bg-[#FFEBEE] text-[#F44336] text-sm rounded-xl p-3">{error}</div>
          )}

          {/* Assign Section */}
          {canAssign && (
            <div className="bg-[#FFF8E1] rounded-xl p-4 space-y-3">
              <p className="text-sm font-semibold text-[#2D2D2D]">Assegna Driver</p>
              <select
                value={selectedDriverId}
                onChange={(e) => setSelectedDriverId(e.target.value)}
                className="w-full px-3 py-2.5 bg-white border border-[#E0E0E0] rounded-xl text-sm text-[#2D2D2D] outline-none focus:border-[#FF8C00] transition-colors"
              >
                <option value="">Seleziona un driver...</option>
                {drivers.map((d) => (
                  <option key={d.user_id} value={d.user_id}>
                    {d.first_name} {d.last_name} — {d.vehicle_make} {d.vehicle_model} ({d.vehicle_plate})
                  </option>
                ))}
              </select>
              <button
                onClick={handleAssign}
                disabled={!selectedDriverId || isAssigning}
                className="w-full py-2.5 bg-[#FF8C00] text-white text-sm font-semibold rounded-xl border-none cursor-pointer hover:bg-[#E07B00] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAssigning ? 'Assegnazione...' : 'Assegna'}
              </button>
            </div>
          )}

          {/* Cancel Section */}
          {canCancel && !showCancelConfirm && (
            <button
              onClick={() => setShowCancelConfirm(true)}
              className="w-full py-2.5 bg-white text-[#F44336] text-sm font-semibold rounded-xl border border-[#F44336] cursor-pointer hover:bg-[#FFEBEE] transition-colors"
            >
              Cancella Corsa
            </button>
          )}

          {showCancelConfirm && (
            <div className="bg-[#FFEBEE] rounded-xl p-4 space-y-3">
              <p className="text-sm font-semibold text-[#F44336]">Conferma Cancellazione</p>
              <textarea
                value={cancelNotes}
                onChange={(e) => setCancelNotes(e.target.value)}
                placeholder="Motivo della cancellazione (opzionale)"
                className="w-full px-3 py-2.5 bg-white border border-[#E0E0E0] rounded-xl text-sm text-[#2D2D2D] outline-none focus:border-[#F44336] resize-none h-20"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => setShowCancelConfirm(false)}
                  className="flex-1 py-2.5 bg-white text-[#666] text-sm font-semibold rounded-xl border border-[#E0E0E0] cursor-pointer hover:bg-[#F5F5F5] transition-colors"
                >
                  Annulla
                </button>
                <button
                  onClick={handleCancel}
                  disabled={isCancelling}
                  className="flex-1 py-2.5 bg-[#F44336] text-white text-sm font-semibold rounded-xl border-none cursor-pointer hover:bg-[#D32F2F] transition-colors disabled:opacity-50"
                >
                  {isCancelling ? 'Cancellazione...' : 'Conferma'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoItem({ label, value, full }: { label: string; value: string; full?: boolean }) {
  return (
    <div className={full ? 'col-span-2' : ''}>
      <p className="text-xs text-[#666] mb-0.5">{label}</p>
      <p className="text-sm text-[#2D2D2D] font-medium">{value}</p>
    </div>
  );
}
