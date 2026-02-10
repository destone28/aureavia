import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

export default function TwoFactorPage() {
  const [code, setCode] = useState('');
  const { verify2FA, isLoading, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await verify2FA(code);
      const { user: loadedUser } = useAuthStore.getState();
      if (loadedUser?.role === 'admin' || loadedUser?.role === 'assistant' || loadedUser?.role === 'finance') {
        navigate('/admin/dashboard');
      } else {
        navigate('/rides');
      }
    } catch {}
  };

  return (
    <div className="min-h-screen bg-[#F5F5F5] flex items-center justify-center p-5 font-['Open_Sans']">
      <div className="w-full max-w-[420px] bg-white p-8 md:p-12 shadow-[0_20px_60px_rgba(45,45,45,0.15)]">
        <div className="text-center mb-8">
          <h1 className="text-[28px] font-semibold text-[#2D2D2D]">AureaVia</h1>
          <p className="text-[#666] text-sm mt-2">Verifica in due passaggi</p>
        </div>

        <p className="text-[#666] text-sm text-center mb-6">
          Abbiamo inviato un codice a 6 cifre alla tua email. Inseriscilo qui sotto per completare l'accesso.
        </p>

        {error && (
          <div className="bg-[#FFEBEE] text-[#F44336] p-3 rounded-lg text-sm mb-4">
            {error}
            <button onClick={clearError} className="float-right font-bold">&#10005;</button>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-5">
            <label className="block text-sm font-medium text-[#666] mb-2">Codice di verifica</label>
            <div className="border border-[#E0E0E0] rounded-xl bg-[#FAFAFA] p-4 focus-within:border-[#FF8C00] focus-within:shadow-[0_0_0_3px_rgba(255,140,0,0.1)] transition-all">
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                className="w-full border-none bg-transparent outline-none text-2xl text-center text-[#2D2D2D] tracking-[0.5em] placeholder:text-[#999] placeholder:tracking-[0.5em]"
                maxLength={6}
                inputMode="numeric"
                autoComplete="one-time-code"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || code.length !== 6}
            className="w-full bg-[#FF8C00] text-white font-semibold text-base py-4 rounded-xl border-none cursor-pointer hover:bg-[#E67E00] hover:-translate-y-0.5 hover:shadow-[0_8px_20px_rgba(255,140,0,0.3)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Verifica in corso...' : 'Verifica'}
          </button>
        </form>

        <button
          onClick={() => navigate('/login')}
          className="w-full mt-4 bg-transparent text-[#666] font-medium text-sm py-3 border-none cursor-pointer hover:text-[#FF8C00] transition-colors"
        >
          Torna al login
        </button>
      </div>
    </div>
  );
}
