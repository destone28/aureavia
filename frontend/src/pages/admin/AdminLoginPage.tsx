import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

export default function AdminLoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/admin/verify-2fa');
    } catch {}
  };

  return (
    <div className="min-h-screen bg-[#F5F5F5] flex items-center justify-center p-5 font-['Open_Sans']">
      <div className="w-full max-w-[420px] bg-white p-8 md:p-12 shadow-[0_20px_60px_rgba(45,45,45,0.15)]">
        <div className="text-center mb-8">
          <h1 className="text-[28px] font-semibold text-[#2D2D2D]">AureaVia</h1>
          <p className="text-[#666] text-sm mt-2">Pannello Amministrazione</p>
        </div>

        {error && (
          <div className="bg-[#FFEBEE] text-[#F44336] p-3 rounded-lg text-sm mb-4">
            {error}
            <button onClick={clearError} className="float-right font-bold">&#10005;</button>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-5">
            <label className="block text-sm font-medium text-[#666] mb-2">Email</label>
            <div className="border border-[#E0E0E0] rounded-xl bg-[#FAFAFA] p-4 focus-within:border-[#FF8C00] focus-within:shadow-[0_0_0_3px_rgba(255,140,0,0.1)] transition-all">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@aureavia.com"
                className="w-full border-none bg-transparent outline-none text-base text-[#2D2D2D] placeholder:text-[#999]"
                required
              />
            </div>
          </div>

          <div className="mb-5">
            <label className="block text-sm font-medium text-[#666] mb-2">Password</label>
            <div className="border border-[#E0E0E0] rounded-xl bg-[#FAFAFA] p-4 focus-within:border-[#FF8C00] focus-within:shadow-[0_0_0_3px_rgba(255,140,0,0.1)] transition-all">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full border-none bg-transparent outline-none text-base text-[#2D2D2D] placeholder:text-[#999]"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-[#FF8C00] text-white font-semibold text-base py-4 rounded-xl border-none cursor-pointer hover:bg-[#E67E00] hover:-translate-y-0.5 hover:shadow-[0_8px_20px_rgba(255,140,0,0.3)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Accesso in corso...' : 'Accedi'}
          </button>
        </form>
      </div>
    </div>
  );
}
