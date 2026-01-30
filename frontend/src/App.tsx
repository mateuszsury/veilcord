import { useEffect, useState } from 'react';
import { ThemeProvider } from '@/components/theme-provider';
import { AppLayout } from '@/components/layout/AppLayout';
import { waitForPyWebView, getApi } from '@/lib/pywebview';
import { useIdentityStore } from '@/stores/identity';
import { useContactsStore } from '@/stores/contacts';

function AppContent() {
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setIdentity = useIdentityStore((s) => s.setIdentity);
  const setIdentityLoading = useIdentityStore((s) => s.setLoading);
  const setContacts = useContactsStore((s) => s.setContacts);

  useEffect(() => {
    async function initialize() {
      try {
        // Wait for PyWebView bridge
        await waitForPyWebView();
        const api = getApi();

        // Load identity
        setIdentityLoading(true);
        const identity = await api.get_identity();
        setIdentity(identity);

        // Load contacts
        const contacts = await api.get_contacts();
        setContacts(contacts);

        setIsReady(true);
      } catch (err) {
        console.error('Initialization error:', err);
        setError(err instanceof Error ? err.message : 'Failed to initialize');
      }
    }

    initialize();
  }, [setIdentity, setIdentityLoading, setContacts]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-cosmic-bg text-red-400">
        <div className="text-center p-8">
          <h1 className="text-xl font-semibold mb-2">Initialization Error</h1>
          <p className="text-cosmic-muted">{error}</p>
        </div>
      </div>
    );
  }

  if (!isReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-cosmic-bg">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-cosmic-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-cosmic-muted">Loading DiscordOpus...</p>
        </div>
      </div>
    );
  }

  return <AppLayout />;
}

export default function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}
