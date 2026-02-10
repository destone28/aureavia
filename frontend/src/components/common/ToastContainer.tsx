import { useUIStore } from '../../store/uiStore';

export function ToastContainer() {
  const { toasts, removeToast } = useUIStore();

  if (toasts.length === 0) return null;

  const borderColors = {
    success: 'border-l-[#4CAF50]',
    error: 'border-l-[#F44336]',
    info: 'border-l-[#2196F3]',
  };

  const icons = {
    success: '✓',
    error: '✕',
    info: 'ℹ',
  };

  return (
    <div className="fixed top-20 right-5 z-[9999] flex flex-col gap-3 max-w-[400px]">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`bg-white rounded-lg p-4 flex items-center gap-3 shadow-[0_4px_12px_rgba(0,0,0,0.15)] min-w-[300px] border-l-4 ${borderColors[toast.type]} animate-[slideInRight_0.3s_ease-out]`}
        >
          <span className="text-lg">{icons[toast.type]}</span>
          <span className="flex-1 text-sm font-semibold text-[#2D2D2D]">
            {toast.message}
          </span>
          <button
            onClick={() => removeToast(toast.id)}
            className="w-5 h-5 border-none bg-transparent cursor-pointer text-[#666] hover:text-[#2D2D2D]"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
