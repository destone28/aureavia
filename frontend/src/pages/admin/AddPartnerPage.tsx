import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '../../store/uiStore';
import api from '../../config/api';

interface PartnerFormData {
  name: string;
  contact_person: string;
  contact_email: string;
  contact_phone: string;
}

const initialFormData: PartnerFormData = {
  name: '',
  contact_person: '',
  contact_email: '',
  contact_phone: '',
};

const inputClasses =
  'w-full border border-[#E0E0E0] rounded-xl bg-[#FAFAFA] p-3 text-sm text-[#2D2D2D] outline-none transition-all focus:border-[#FF8C00] focus:shadow-[0_0_0_3px_rgba(255,140,0,0.1)]';
const labelClasses = 'block text-sm font-medium text-[#666] mb-2';

export default function AddPartnerPage() {
  const navigate = useNavigate();
  const addToast = useUIStore((s) => s.addToast);

  const [form, setForm] = useState<PartnerFormData>(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!form.name.trim()) {
      addToast('error', 'Il nome della societa è obbligatorio');
      return;
    }
    if (!form.contact_email.trim()) {
      addToast('error', 'L\'email di contatto è obbligatoria');
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        name: form.name.trim(),
        contact_email: form.contact_email.trim(),
      };

      if (form.contact_person.trim()) payload.contact_person = form.contact_person.trim();
      if (form.contact_phone.trim()) payload.contact_phone = form.contact_phone.trim();

      await api.post('/companies/', payload);

      addToast('success', 'Partner NCC creato con successo');
      navigate('/admin/dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      addToast('error', typeof detail === 'string' ? detail : 'Errore nella creazione del partner');
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
        <h2 className="text-2xl font-bold text-[#2D2D2D] mb-6">Aggiungi Partner NCC</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-white rounded-2xl p-6 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
            <h3 className="text-lg font-semibold text-[#2D2D2D] mb-4">Dati Societa</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label htmlFor="name" className={labelClasses}>Nome Societa *</label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  value={form.name}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="NCC Roma Trasporti S.r.l."
                  required
                />
              </div>
              <div>
                <label htmlFor="contact_person" className={labelClasses}>Referente</label>
                <input
                  id="contact_person"
                  name="contact_person"
                  type="text"
                  value={form.contact_person}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="Mario Rossi"
                />
              </div>
              <div>
                <label htmlFor="contact_email" className={labelClasses}>Email Contatto *</label>
                <input
                  id="contact_email"
                  name="contact_email"
                  type="email"
                  value={form.contact_email}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="info@ncctrasporti.it"
                  required
                />
              </div>
              <div className="sm:col-span-2">
                <label htmlFor="contact_phone" className={labelClasses}>Telefono</label>
                <input
                  id="contact_phone"
                  name="contact_phone"
                  type="tel"
                  value={form.contact_phone}
                  onChange={handleChange}
                  className={inputClasses}
                  placeholder="+39 06 1234567"
                />
              </div>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-[#FF8C00] text-white font-semibold py-4 rounded-xl border-none cursor-pointer text-base hover:bg-[#E07B00] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Creazione in corso...' : 'Crea Partner'}
          </button>
        </form>
      </main>
    </div>
  );
}
