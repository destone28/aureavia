import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../config/api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.post('/auth/forgot-password', { email });
      setSent(true);
    } catch {
      setError('Errore nell\'invio. Riprova.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F5] flex items-center justify-center p-4 font-['Open_Sans']">
      <div className="bg-white rounded-2xl shadow-[0_4px_16px_rgba(0,0,0,0.06)] p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-[#2D2D2D] mb-2">
          <span className="text-[#FF8C00]">AureaVia</span>
        </h1>
        <h2 className="text-lg font-semibold text-[#2D2D2D] mb-6">Recupera Password</h2>

        {sent ? (
          <div className="space-y-4">
            <div className="bg-[#E8F5E9] text-[#4CAF50] rounded-xl p-4 text-sm">
              Se l'email esiste, riceverai un codice di reset. Controlla la tua casella email.
            </div>
            <button
              onClick={() => navigate('/reset-password', { state: { email } })}
              className="w-full py-3 bg-[#FF8C00] text-white text-sm font-semibold rounded-xl border-none cursor-pointer hover:bg-[#E07B00] transition-colors"
            >
              Inserisci Codice di Reset
            </button>
            <button
              onClick={() => navigate('/login')}
              className="w-full py-3 bg-transparent text-[#666] text-sm font-medium border-none cursor-pointer hover:text-[#2D2D2D] transition-colors"
            >
              Torna al Login
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <p className="text-sm text-[#666]">
              Inserisci la tua email per ricevere un codice di reset della password.
            </p>
            <div>
              <label className="block text-sm font-medium text-[#2D2D2D] mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-[#F5F5F5] border border-[#E0E0E0] rounded-xl text-sm text-[#2D2D2D] outline-none focus:border-[#FF8C00] transition-colors"
                placeholder="nome@email.com"
              />
            </div>
            {error && <p className="text-sm text-[#F44336]">{error}</p>}
            <button
              type="submit"
              disabled={loading || !email}
              className="w-full py-3 bg-[#FF8C00] text-white text-sm font-semibold rounded-xl border-none cursor-pointer hover:bg-[#E07B00] transition-colors disabled:opacity-50"
            >
              {loading ? 'Invio...' : 'Invia Codice'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="w-full py-3 bg-transparent text-[#666] text-sm font-medium border-none cursor-pointer hover:text-[#2D2D2D] transition-colors"
            >
              Torna al Login
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
