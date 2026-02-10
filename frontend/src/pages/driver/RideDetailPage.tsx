import { useNavigate } from 'react-router-dom';

export default function RideDetailPage() {
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
        <h1 className="text-lg font-semibold">Dettaglio Corsa</h1>
        <div className="w-8" />
      </header>

      {/* Content */}
      <main className="p-5">
        <div className="bg-white rounded-2xl p-8 shadow-[0_4px_16px_rgba(0,0,0,0.06)] text-center">
          <div className="text-5xl mb-4 text-[#FF8C00]">&#128205;</div>
          <h2 className="text-xl font-semibold text-[#2D2D2D] mb-2">Dettaglio corsa</h2>
          <p className="text-[#666] text-sm">
            I dettagli della corsa selezionata appariranno qui.
          </p>
          <div className="mt-6 inline-block bg-[#FFF3E0] text-[#FF8C00] font-medium text-sm px-4 py-2 rounded-lg">
            In arrivo
          </div>
        </div>
      </main>
    </div>
  );
}
