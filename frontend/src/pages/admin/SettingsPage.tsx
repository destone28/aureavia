import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useUIStore } from '../../store/uiStore';
import {
  fetchBookingConfig,
  updateBookingConfig,
  testBookingConnection,
  syncBookings,
} from '../../services/bookingConfigService';
import type { BookingConfig } from '../../services/bookingConfigService';

export default function SettingsPage() {
  const navigate = useNavigate();
  const { logout, user } = useAuthStore();
  const addToast = useUIStore((s) => s.addToast);

  const [config, setConfig] = useState<BookingConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [syncing, setSyncing] = useState(false);

  // Form state
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [webhookSecret, setWebhookSecret] = useState('');
  const [environment, setEnvironment] = useState('sandbox');
  const [isEnabled, setIsEnabled] = useState(false);

  const loadConfig = useCallback(async () => {
    try {
      const data = await fetchBookingConfig();
      setConfig(data);
      setClientId(data.client_id);
      setWebhookSecret(data.webhook_secret);
      setEnvironment(data.environment);
      setIsEnabled(data.is_enabled);
    } catch {
      addToast('error', 'Errore nel caricamento della configurazione');
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const update: Record<string, string | boolean> = {
        client_id: clientId,
        webhook_secret: webhookSecret,
        environment,
        is_enabled: isEnabled,
      };
      if (clientSecret) {
        update.client_secret = clientSecret;
      }
      const data = await updateBookingConfig(update);
      setConfig(data);
      setClientSecret('');
      addToast('success', 'Configurazione salvata con successo');
    } catch {
      addToast('error', 'Errore nel salvataggio della configurazione');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const result = await testBookingConnection();
      if (result.success) {
        addToast('success', result.message);
      } else {
        addToast('error', result.message);
      }
    } catch {
      addToast('error', 'Errore durante il test della connessione');
    } finally {
      setTesting(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await syncBookings();
      if (result.success) {
        addToast('success', result.message);
      } else {
        addToast('error', result.message);
      }
    } catch {
      addToast('error', 'Errore durante la sincronizzazione');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F5] font-['Open_Sans']">
      {/* Header */}
      <header className="bg-white border-b border-[#E0E0E0] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/admin/dashboard')}
            className="flex items-center gap-2 text-[#666] hover:text-[#2D2D2D] bg-transparent border-none cursor-pointer transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <h1 className="text-xl font-semibold text-[#2D2D2D]">
            <span className="text-[#FF8C00]">AureaVia</span> Impostazioni
          </h1>
        </div>
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

      <main className="max-w-[800px] mx-auto p-6 space-y-6">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-10 h-10 border-4 border-[#FF8C00] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {/* Booking.com Integration Card */}
            <div className="bg-white rounded-2xl p-6 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-[#2D2D2D]">Integrazione Booking.com</h2>
                  <p className="text-sm text-[#666] mt-1">
                    Configura le credenziali per ricevere prenotazioni da Booking.com
                  </p>
                </div>
                {/* Enable toggle */}
                <button
                  onClick={() => setIsEnabled(!isEnabled)}
                  className={`relative w-12 h-7 rounded-full transition-colors cursor-pointer border-none ${
                    isEnabled ? 'bg-[#4CAF50]' : 'bg-[#E0E0E0]'
                  }`}
                >
                  <span
                    className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                      isEnabled ? 'left-6' : 'left-1'
                    }`}
                  />
                </button>
              </div>

              {/* Status indicator */}
              <div className="flex items-center gap-2 mb-6 p-3 rounded-xl bg-[#F5F5F5]">
                <div className={`w-2.5 h-2.5 rounded-full ${
                  isEnabled && config?.has_client_secret ? 'bg-[#4CAF50]' : 'bg-[#E0E0E0]'
                }`} />
                <span className="text-sm text-[#666]">
                  {isEnabled && config?.has_client_secret
                    ? 'Integrazione attiva'
                    : isEnabled
                      ? 'Credenziali mancanti'
                      : 'Integrazione disabilitata'}
                </span>
                {config?.last_sync_at && (
                  <span className="text-xs text-[#999] ml-auto">
                    Ultima sync: {new Date(config.last_sync_at).toLocaleString('it-IT')}
                  </span>
                )}
              </div>

              {/* Environment selector */}
              <div className="mb-5">
                <label className="block text-sm font-medium text-[#2D2D2D] mb-2">Ambiente</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setEnvironment('sandbox')}
                    className={`flex-1 py-2.5 rounded-xl text-sm font-medium border-2 cursor-pointer transition-colors ${
                      environment === 'sandbox'
                        ? 'border-[#FF8C00] bg-[#FFF5E6] text-[#FF8C00]'
                        : 'border-[#E0E0E0] bg-white text-[#666] hover:border-[#ccc]'
                    }`}
                  >
                    Sandbox
                  </button>
                  <button
                    onClick={() => setEnvironment('production')}
                    className={`flex-1 py-2.5 rounded-xl text-sm font-medium border-2 cursor-pointer transition-colors ${
                      environment === 'production'
                        ? 'border-[#FF8C00] bg-[#FFF5E6] text-[#FF8C00]'
                        : 'border-[#E0E0E0] bg-white text-[#666] hover:border-[#ccc]'
                    }`}
                  >
                    Produzione
                  </button>
                </div>
              </div>

              {/* Client ID */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-[#2D2D2D] mb-2">Client ID</label>
                <input
                  type="text"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  placeholder="Inserisci il Client ID di Booking.com"
                  className="w-full px-4 py-3 rounded-xl border border-[#E0E0E0] text-sm text-[#2D2D2D] placeholder-[#999] outline-none focus:border-[#FF8C00] transition-colors"
                />
              </div>

              {/* Client Secret */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-[#2D2D2D] mb-2">
                  Client Secret
                  {config?.has_client_secret && (
                    <span className="ml-2 text-xs text-[#4CAF50] font-normal">Configurato</span>
                  )}
                </label>
                <input
                  type="password"
                  value={clientSecret}
                  onChange={(e) => setClientSecret(e.target.value)}
                  placeholder={config?.has_client_secret ? 'Lascia vuoto per mantenere il valore attuale' : 'Inserisci il Client Secret'}
                  className="w-full px-4 py-3 rounded-xl border border-[#E0E0E0] text-sm text-[#2D2D2D] placeholder-[#999] outline-none focus:border-[#FF8C00] transition-colors"
                />
              </div>

              {/* Webhook Secret */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-[#2D2D2D] mb-2">Webhook Secret</label>
                <input
                  type="text"
                  value={webhookSecret}
                  onChange={(e) => setWebhookSecret(e.target.value)}
                  placeholder="Secret per validare i webhook in arrivo (opzionale)"
                  className="w-full px-4 py-3 rounded-xl border border-[#E0E0E0] text-sm text-[#2D2D2D] placeholder-[#999] outline-none focus:border-[#FF8C00] transition-colors"
                />
                <p className="text-xs text-[#999] mt-1">
                  Se vuoto, tutti i webhook saranno accettati (solo per sviluppo)
                </p>
              </div>

              {/* Save button */}
              <button
                onClick={handleSave}
                disabled={saving}
                className="w-full py-3 rounded-xl bg-[#FF8C00] text-white text-sm font-semibold border-none cursor-pointer hover:bg-[#E07B00] transition-colors disabled:opacity-50"
              >
                {saving ? 'Salvataggio...' : 'Salva configurazione'}
              </button>
            </div>

            {/* Actions Card */}
            <div className="bg-white rounded-2xl p-6 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
              <h2 className="text-lg font-semibold text-[#2D2D2D] mb-4">Azioni</h2>

              <div className="space-y-3">
                {/* Test Connection */}
                <div className="flex items-center justify-between p-4 rounded-xl bg-[#F5F5F5]">
                  <div>
                    <p className="text-sm font-medium text-[#2D2D2D]">Test connessione</p>
                    <p className="text-xs text-[#666] mt-0.5">
                      Verifica le credenziali OAuth2 con Booking.com
                    </p>
                  </div>
                  <button
                    onClick={handleTest}
                    disabled={testing || !clientId}
                    className="px-5 py-2.5 rounded-xl bg-[#2196F3] text-white text-sm font-semibold border-none cursor-pointer hover:bg-[#1976D2] transition-colors disabled:opacity-50"
                  >
                    {testing ? (
                      <span className="flex items-center gap-2">
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Test...
                      </span>
                    ) : (
                      'Testa'
                    )}
                  </button>
                </div>

                {/* Manual Sync */}
                <div className="flex items-center justify-between p-4 rounded-xl bg-[#F5F5F5]">
                  <div>
                    <p className="text-sm font-medium text-[#2D2D2D]">Sincronizzazione manuale</p>
                    <p className="text-xs text-[#666] mt-0.5">
                      Scarica nuove prenotazioni da Booking.com
                    </p>
                  </div>
                  <button
                    onClick={handleSync}
                    disabled={syncing || !isEnabled}
                    className="px-5 py-2.5 rounded-xl bg-[#4CAF50] text-white text-sm font-semibold border-none cursor-pointer hover:bg-[#43A047] transition-colors disabled:opacity-50"
                  >
                    {syncing ? (
                      <span className="flex items-center gap-2">
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Sync...
                      </span>
                    ) : (
                      'Sincronizza'
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Webhook Info Card */}
            <div className="bg-white rounded-2xl p-6 shadow-[0_4px_16px_rgba(0,0,0,0.06)]">
              <h2 className="text-lg font-semibold text-[#2D2D2D] mb-4">Endpoint Webhook</h2>
              <p className="text-sm text-[#666] mb-4">
                Configura questi URL nel pannello Booking.com Taxi Supplier:
              </p>
              <div className="space-y-2">
                {[
                  { method: 'POST', path: '/api/webhook/booking/search', desc: 'Ricerca prezzo' },
                  { method: 'POST', path: '/api/webhook/booking/new', desc: 'Nuova prenotazione' },
                  { method: 'PATCH', path: '/api/webhook/booking/{ref}', desc: 'Modifica/Cancellazione' },
                  { method: 'POST', path: '/api/webhook/booking/incident', desc: 'Incidenti' },
                ].map((ep) => (
                  <div key={ep.path} className="flex items-center gap-3 p-3 rounded-lg bg-[#F5F5F5] font-mono text-xs">
                    <span className={`px-2 py-0.5 rounded font-semibold ${
                      ep.method === 'POST' ? 'bg-[#E8F5E9] text-[#4CAF50]' : 'bg-[#FFF3E0] text-[#FF8C00]'
                    }`}>
                      {ep.method}
                    </span>
                    <span className="text-[#2D2D2D] flex-1">{ep.path}</span>
                    <span className="text-[#999] font-sans">{ep.desc}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
