import { useNavigate } from 'react-router-dom';

export default function ProfilePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F5F5F5] font-['Open_Sans']">
      {/* Header */}
      <header className="bg-[#FF8C00] text-white px-5 py-4 flex items-center justify-between shadow-[0_2px_8px_rgba(0,0,0,0.1)]">
        <button
          onClick={() => navigate('/rides')}
          className="text-white text-2xl bg-transparent border-none cursor-pointer"
        >
          &#8592;
        </button>
        <h1 className="text-lg font-semibold">Profilo</h1>
        <div className="w-8" />
      </header>

      {/* Content */}
      <main className="p-5">
        <div className="bg-white rounded-2xl p-8 shadow-[0_4px_16px_rgba(0,0,0,0.06)] text-center">
          <div className="text-5xl mb-4 text-[#FF8C00]">&#128100;</div>
          <h2 className="text-xl font-semibold text-[#2D2D2D] mb-2">Il tuo profilo</h2>
          <p className="text-[#666] text-sm">
            Dati anagrafici, veicolo, attivit&agrave; e recensioni appariranno qui.
          </p>
          <div className="mt-6 inline-block bg-[#FFF3E0] text-[#FF8C00] font-medium text-sm px-4 py-2 rounded-lg">
            In arrivo
          </div>
        </div>
      </main>
    </div>
  );
}
