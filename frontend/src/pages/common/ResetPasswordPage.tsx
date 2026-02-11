import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../../config/api';

export default function ResetPasswordPage() {
  const location = useLocation();
  const [email, setEmail] = useState((location.state as { email?: string })?.email || '');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (newPassword.length < 6) {
      setError('La password deve essere di almeno 6 caratteri');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Le password non corrispondono');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/reset-password', {
        token: `${email}:${code}`,
        new_password: newPassword,
      });
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore nel reset. Riprova.');
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
        <h2 className="text-lg font-semibold text-[#2D2D2D] mb-6">Reimposta Password</h2>

        {success ? (
          <div className="space-y-4">
            <div className="bg-[#E8F5E9] text-[#4CAF50] rounded-xl p-4 text-sm">
              Password reimpostata con successo!
            </div>
            <button
              onClick={() => navigate('/login')}
              className="w-full py-3 bg-[#FF8C00] text-white text-sm font-semibold rounded-xl border-none cursor-pointer hover:bg-[#E07B00] transition-colors"
            >
              Vai al Login
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#2D2D2D] mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-[#F5F5F5] border border-[#E0E0E0] rounded-xl text-sm text-[#2D2D2D] outline-none focus:border-[#FF8C00] transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#2D2D2D] mb-1">Codice di Reset</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                maxLength={6}
                className="w-full px-4 py-3 bg-[#F5F5F5] border border-[#E0E0E0] rounded-xl text-sm text-[#2D2D2D] outline-none focus:border-[#FF8C00] transition-colors text-center tracking-[8px] text-lg font-bold"
                placeholder="000000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#2D2D2D] mb-1">Nuova Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={6}
                className="w-full px-4 py-3 bg-[#F5F5F5] border border-[#E0E0E0] rounded-xl text-sm text-[#2D2D2D] outline-none focus:border-[#FF8C00] transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#2D2D2D] mb-1">Conferma Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full px-4 py-3 bg-[#F5F5F5] border border-[#E0E0E0] rounded-xl text-sm text-[#2D2D2D] outline-none focus:border-[#FF8C00] transition-colors"
              />
            </div>
            {error && <p className="text-sm text-[#F44336]">{error}</p>}
            <button
              type="submit"
              disabled={loading || !email || !code || !newPassword || !confirmPassword}
              className="w-full py-3 bg-[#FF8C00] text-white text-sm font-semibold rounded-xl border-none cursor-pointer hover:bg-[#E07B00] transition-colors disabled:opacity-50"
            >
              {loading ? 'Reset...' : 'Reimposta Password'}
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
