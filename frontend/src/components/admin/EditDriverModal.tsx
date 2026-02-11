import { useState } from 'react';
import api from '../../config/api';
import type { DriverListItem } from '../../services/adminService';

interface Props {
  driver: DriverListItem;
  onClose: () => void;
  onSaved: () => void;
}

export default function EditDriverModal({ driver, onClose, onSaved }: Props) {
  const [form, setForm] = useState({
    vehicle_make: driver.vehicle_make || '',
    vehicle_model: driver.vehicle_model || '',
    vehicle_plate: driver.vehicle_plate || '',
    vehicle_seats: 4,
    vehicle_luggage_capacity: 2,
    vehicle_fuel_type: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field: string, value: string | number) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      await api.put(`/drivers/${driver.id}`, form);
      onSaved();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore nel salvataggio');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b border-[#E0E0E0]">
          <h2 className="text-lg font-semibold text-[#2D2D2D]">
            Modifica Driver - {driver.first_name} {driver.last_name}
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#F5F5F5] text-[#666] border-none cursor-pointer hover:bg-[#E0E0E0]"
          >
            &times;
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Marca" value={form.vehicle_make} onChange={(v) => handleChange('vehicle_make', v)} />
            <Field label="Modello" value={form.vehicle_model} onChange={(v) => handleChange('vehicle_model', v)} />
            <Field label="Targa" value={form.vehicle_plate} onChange={(v) => handleChange('vehicle_plate', v)} />
            <div>
              <label className="block text-xs text-[#666] mb-1">Posti</label>
              <input
                type="number"
                value={form.vehicle_seats}
                onChange={(e) => handleChange('vehicle_seats', parseInt(e.target.value) || 0)}
                min={1}
                max={50}
                className="w-full px-3 py-2.5 bg-[#F5F5F5] border border-[#E0E0E0] rounded-xl text-sm outline-none focus:border-[#FF8C00]"
              />
            </div>
            <Field
              label="Capienza Bagagli"
              value={String(form.vehicle_luggage_capacity)}
              onChange={(v) => handleChange('vehicle_luggage_capacity', parseInt(v) || 0)}
            />
            <div>
              <label className="block text-xs text-[#666] mb-1">Carburante</label>
              <select
                value={form.vehicle_fuel_type}
                onChange={(e) => handleChange('vehicle_fuel_type', e.target.value)}
                className="w-full px-3 py-2.5 bg-[#F5F5F5] border border-[#E0E0E0] rounded-xl text-sm outline-none focus:border-[#FF8C00]"
              >
                <option value="">—</option>
                <option value="diesel">Diesel</option>
                <option value="gasoline">Benzina</option>
                <option value="hybrid">Ibrido</option>
                <option value="electric">Elettrico</option>
                <option value="lpg">GPL</option>
                <option value="cng">Metano</option>
              </select>
            </div>
          </div>

          {error && <p className="text-sm text-[#F44336]">{error}</p>}

          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 py-2.5 bg-white text-[#666] text-sm font-semibold rounded-xl border border-[#E0E0E0] cursor-pointer hover:bg-[#F5F5F5]"
            >
              Annulla
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 py-2.5 bg-[#FF8C00] text-white text-sm font-semibold rounded-xl border-none cursor-pointer hover:bg-[#E07B00] disabled:opacity-50"
            >
              {saving ? 'Salvataggio...' : 'Salva'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="block text-xs text-[#666] mb-1">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2.5 bg-[#F5F5F5] border border-[#E0E0E0] rounded-xl text-sm outline-none focus:border-[#FF8C00]"
      />
    </div>
  );
}
