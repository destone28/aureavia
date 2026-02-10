import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '../../store/uiStore';
import { fetchCompaniesList } from '../../services/adminService';
import type { CompanyListItem } from '../../services/adminService';
import api from '../../config/api';

interface DriverFormData {
  // User fields
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  password: string;
  // Driver fields
  ncc_company_id: string;
  license_number: string;
  license_expiry: string;
  vehicle_make: string;
  vehicle_model: string;
  vehicle_plate: string;
  vehicle_year: string;
  vehicle_seats: string;
  vehicle_luggage_capacity: string;
  vehicle_fuel_type: string;
  // Insurance fields
  insurance_number: string;
  insurance_expiry: string;
  vehicle_inspection_date: string;
}

const initialFormData: DriverFormData = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  password: '',
  ncc_company_id: '',
  license_number: '',
  license_expiry: '',
  vehicle_make: '',
  vehicle_model: '',
  vehicle_plate: '',
  vehicle_year: '',
  vehicle_seats: '',
  vehicle_luggage_capacity: '',
  vehicle_fuel_type: '',
  insurance_number: '',
  insurance_expiry: '',
  vehicle_inspection_date: '',
};

const inputClasses =
  'w-full border border-[#E0E0E0] rounded-xl bg-[#FAFAFA] p-3 text-sm text-[#2D2D2D] outline-none transition-all focus:border-[#FF8C00] focus:shadow-[0_0_0_3px_rgba(255,140,0,0.1)]';
const labelClasses = 'block text-sm font-medium text-[#666] mb-2';

export default function AddDriverPage() {
  const navigate = useNavigate();
  const addToast = useUIStore((s) => s.addToast);

  const [form, setForm] = useState<DriverFormData>(initialFormData);
  const [companies, setCompanies] = useState<CompanyListItem[]>([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchCompaniesList();
        if (!cancelled) setCompanies(data);
      } catch {
        // Silently fail; dropdown will just be empty
      }
    })();
    return () => { cancelled = true; };
  }, []);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    // Basic validation
    if (!form.first_name.trim() || !form.last_name.trim()) {
      addToast('error', 'Nome e cognome sono obbligatori');
      return;
    }
    if (!form.email.trim()) {
      addToast('error', 'Email è obbligatoria');
      return;
    }
    if (!form.password.trim() || form.password.length < 6) {
      addToast('error', 'La password deve essere di almeno 6 caratteri');
      return;
    }
    if (!form.license_number.trim()) {
      addToast('error', 'Numero patente è obbligatorio');
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        password: form.password,
        license_number: form.license_number.trim(),
      };

      if (form.phone.trim()) payload.phone = form.phone.trim();
      if (form.ncc_company_id) payload.ncc_company_id = form.ncc_company_id;
      if (form.license_expiry) payload.license_expiry = form.license_expiry;
      if (form.vehicle_make.trim()) payload.vehicle_make = form.vehicle_make.trim();
      if (form.vehicle_model.trim()) payload.vehicle_model = form.vehicle_model.trim();
      if (form.vehicle_plate.trim()) payload.vehicle_plate = form.vehicle_plate.trim();
      if (form.vehicle_year) payload.vehicle_year = parseInt(form.vehicle_year, 10);
      if (form.vehicle_seats) payload.vehicle_seats = parseInt(form.vehicle_seats, 10);
      if (form.vehicle_luggage_capacity) payload.vehicle_luggage_capacity = parseInt(form.vehicle_luggage_capacity, 10);
      if (form.vehicle_fuel_type.trim()) payload.vehicle_fuel_type = form.vehicle_fuel_type.trim();
      if (form.insurance_number.trim()) payload.insurance_number = form.insurance_number.trim();

      await api.post('/drivers/', payload);

      addToast('success', 'Driver creato con successo');
      navigate('/admin/dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      addToast('error', typeof detail === 'string' ? detail : 'Errore nella creazione del driver');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#F5F5F5] font-['Open_Sans']">
      {/* Header */}
      <header className="bg-white border-b border-[#E0E0E0] px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => navigate('/admin/dashboard')}
          className="text-sm text-[#666] hover:text-[#2D2D2D] bg-transparent border-none cursor-pointer transition-colors flex items-center gap-1"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Indietro
        </button>
        <h1 className="text-xl font-semibold text-[#2D2D2D]">
          <span className="text-[#FF8C00]">AureaVia</span> Admin
        </h1>
      </header>

      {/* Content */}
      <main className="max-w-3xl mx-auto p-6">
        <h2 className="text-2xl font-bold text-[#2D2D2D] mb-6">Aggiungi Driver</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* User info section */}
          <div className="bg-white rounded-2xl p-6 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
            <h3 className="text-lg font-semibold text-[#2D2D2D] mb-4">Informazioni Personali</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className={labelClasses}>Nome *</label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  value={form.first_name}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="Mario"
                  required
                />
              </div>
              <div>
                <label htmlFor="last_name" className={labelClasses}>Cognome *</label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  value={form.last_name}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="Rossi"
                  required
                />
              </div>
              <div>
                <label htmlFor="email" className={labelClasses}>Email *</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="mario.rossi@email.com"
                  required
                />
              </div>
              <div>
                <label htmlFor="phone" className={labelClasses}>Telefono</label>
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  value={form.phone}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="+39 333 1234567"
                />
              </div>
              <div className="sm:col-span-2">
                <label htmlFor="password" className={labelClasses}>Password *</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  value={form.password}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="Minimo 6 caratteri"
                  required
                  minLength={6}
                />
              </div>
            </div>
          </div>

          {/* Driver / Vehicle info section */}
          <div className="bg-white rounded-2xl p-6 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
            <h3 className="text-lg font-semibold text-[#2D2D2D] mb-4">Patente e Veicolo</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="license_number" className={labelClasses}>Numero Patente *</label>
                <input
                  id="license_number"
                  name="license_number"
                  type="text"
                  value={form.license_number}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="AB12345CD"
                  required
                />
              </div>
              <div>
                <label htmlFor="license_expiry" className={labelClasses}>Scadenza Patente</label>
                <input
                  id="license_expiry"
                  name="license_expiry"
                  type="date"
                  value={form.license_expiry}
                  onChange={handleChange}
                  className={inputClasses}
                />
              </div>
              <div>
                <label htmlFor="vehicle_make" className={labelClasses}>Marca Veicolo</label>
                <input
                  id="vehicle_make"
                  name="vehicle_make"
                  type="text"
                  value={form.vehicle_make}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="Mercedes-Benz"
                />
              </div>
              <div>
                <label htmlFor="vehicle_model" className={labelClasses}>Modello Veicolo</label>
                <input
                  id="vehicle_model"
                  name="vehicle_model"
                  type="text"
                  value={form.vehicle_model}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="Classe E"
                />
              </div>
              <div>
                <label htmlFor="vehicle_plate" className={labelClasses}>Targa</label>
                <input
                  id="vehicle_plate"
                  name="vehicle_plate"
                  type="text"
                  value={form.vehicle_plate}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="AA000BB"
                />
              </div>
              <div>
                <label htmlFor="vehicle_year" className={labelClasses}>Anno Veicolo</label>
                <input
                  id="vehicle_year"
                  name="vehicle_year"
                  type="number"
                  value={form.vehicle_year}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="2024"
                  min={1990}
                  max={2030}
                />
              </div>
              <div>
                <label htmlFor="vehicle_seats" className={labelClasses}>Posti a Sedere</label>
                <input
                  id="vehicle_seats"
                  name="vehicle_seats"
                  type="number"
                  value={form.vehicle_seats}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="4"
                  min={1}
                  max={20}
                />
              </div>
              <div>
                <label htmlFor="vehicle_luggage_capacity" className={labelClasses}>Capacita Bagagli</label>
                <input
                  id="vehicle_luggage_capacity"
                  name="vehicle_luggage_capacity"
                  type="number"
                  value={form.vehicle_luggage_capacity}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="2"
                  min={0}
                  max={20}
                />
              </div>
              <div className="sm:col-span-2">
                <label htmlFor="vehicle_fuel_type" className={labelClasses}>Tipo Carburante</label>
                <select
                  id="vehicle_fuel_type"
                  name="vehicle_fuel_type"
                  value={form.vehicle_fuel_type}
                  onChange={handleChange}
                  className={inputClasses}
                >
                  <option value="">Seleziona...</option>
                  <option value="benzina">Benzina</option>
                  <option value="diesel">Diesel</option>
                  <option value="gpl">GPL</option>
                  <option value="metano">Metano</option>
                  <option value="ibrido">Ibrido</option>
                  <option value="elettrico">Elettrico</option>
                </select>
              </div>
            </div>
          </div>

          {/* Insurance section */}
          <div className="bg-white rounded-2xl p-6 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
            <h3 className="text-lg font-semibold text-[#2D2D2D] mb-4">Assicurazione e Revisione</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="insurance_number" className={labelClasses}>Numero Polizza</label>
                <input
                  id="insurance_number"
                  name="insurance_number"
                  type="text"
                  value={form.insurance_number}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="POL-123456"
                />
              </div>
              <div>
                <label htmlFor="insurance_expiry" className={labelClasses}>Scadenza Assicurazione</label>
                <input
                  id="insurance_expiry"
                  name="insurance_expiry"
                  type="date"
                  value={form.insurance_expiry}
                  onChange={handleChange}
                  className={inputClasses}
                />
              </div>
              <div className="sm:col-span-2">
                <label htmlFor="vehicle_inspection_date" className={labelClasses}>Data Revisione</label>
                <input
                  id="vehicle_inspection_date"
                  name="vehicle_inspection_date"
                  type="date"
                  value={form.vehicle_inspection_date}
                  onChange={handleChange}
                  className={inputClasses}
                />
              </div>
            </div>
          </div>

          {/* NCC Company section */}
          <div className="bg-white rounded-2xl p-6 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
            <h3 className="text-lg font-semibold text-[#2D2D2D] mb-4">Societa NCC</h3>
            <div>
              <label htmlFor="ncc_company_id" className={labelClasses}>
                Societa NCC (opzionale - lascia vuoto per driver diretto)
              </label>
              <select
                id="ncc_company_id"
                name="ncc_company_id"
                value={form.ncc_company_id}
                onChange={handleChange}
                className={inputClasses}
              >
                <option value="">Driver diretto (nessuna societa)</option>
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-[#FF8C00] text-white font-semibold py-4 rounded-xl border-none cursor-pointer text-base hover:bg-[#E07B00] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Creazione in corso...' : 'Crea Driver'}
          </button>
        </form>
      </main>
    </div>
  );
}
