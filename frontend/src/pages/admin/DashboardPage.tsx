import { useState } from 'react';
import { useAuthStore } from '../../store/authStore';

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'rides', label: 'Corse' },
  { id: 'drivers', label: 'Driver' },
  { id: 'partners', label: 'Partner' },
] as const;

type TabId = (typeof tabs)[number]['id'];

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const { logout, user } = useAuthStore();

  return (
    <div className="min-h-screen bg-[#F5F5F5] font-['Open_Sans']">
      {/* Header */}
      <header className="bg-white border-b border-[#E0E0E0] px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#2D2D2D]">
          <span className="text-[#FF8C00]">AureaVia</span> Admin
        </h1>
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm text-[#666]">
              {user.first_name} {user.last_name}
            </span>
          )}
          <button
            onClick={logout}
            className="text-sm text-[#666] hover:text-[#F44336] bg-transparent border-none cursor-pointer transition-colors"
          >
            Esci
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-[#E0E0E0] px-6 flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-3 text-sm font-medium border-none bg-transparent cursor-pointer transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'text-[#FF8C00] border-b-2 border-[#FF8C00] shadow-[inset_0_-2px_0_#FF8C00]'
                : 'text-[#666] hover:text-[#2D2D2D]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="p-6">
        <div className="bg-white rounded-2xl p-8 shadow-[0_4px_16px_rgba(0,0,0,0.06)] text-center">
          <div className="text-5xl mb-4 text-[#FF8C00]">&#128202;</div>
          <h2 className="text-xl font-semibold text-[#2D2D2D] mb-2">
            {tabs.find((t) => t.id === activeTab)?.label}
          </h2>
          <p className="text-[#666] text-sm">
            I contenuti della sezione {tabs.find((t) => t.id === activeTab)?.label.toLowerCase()} appariranno qui.
          </p>
          <div className="mt-6 inline-block bg-[#FFF3E0] text-[#FF8C00] font-medium text-sm px-4 py-2 rounded-lg">
            In arrivo
          </div>
        </div>
      </main>
    </div>
  );
}
