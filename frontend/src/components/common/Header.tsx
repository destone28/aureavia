import { useAuthStore } from '../../store/authStore';

interface HeaderProps {
  onMenuToggle: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const user = useAuthStore((s) => s.user);

  const initials = user
    ? `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase()
    : 'AV';

  const fullName = user ? `${user.first_name} ${user.last_name}` : '';

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-[#FF8C00] z-[100] shadow-md flex items-center justify-between px-4">
      {/* Left: Logo */}
      <div className="flex items-center gap-2">
        <span className="text-white font-bold text-lg tracking-wide hidden sm:inline">
          AureaVia
        </span>
        <span className="text-white font-bold text-lg tracking-wide sm:hidden">
          AV
        </span>
      </div>

      {/* Right: User info + Avatar + Hamburger */}
      <div className="flex items-center gap-3">
        {fullName && (
          <span className="text-white text-sm font-semibold hidden sm:inline">
            {fullName}
          </span>
        )}

        {/* Avatar */}
        <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center flex-shrink-0">
          <span className="text-[#FF8C00] font-bold text-sm">{initials}</span>
        </div>

        {/* Hamburger button */}
        <button
          onClick={onMenuToggle}
          className="flex flex-col justify-center items-center w-10 h-10 rounded-lg hover:bg-white/20 transition-colors"
          aria-label="Toggle menu"
        >
          <span className="block w-5 h-0.5 bg-white mb-1 rounded-full" />
          <span className="block w-5 h-0.5 bg-white mb-1 rounded-full" />
          <span className="block w-5 h-0.5 bg-white rounded-full" />
        </button>
      </div>
    </header>
  );
}
