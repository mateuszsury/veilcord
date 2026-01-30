import { useState, useEffect } from 'react';
import { useNetworkStore } from '@/stores/network';

export function NetworkSection() {
  const signalingServer = useNetworkStore((s) => s.signalingServer);
  const connectionState = useNetworkStore((s) => s.connectionState);
  const updateSignalingServer = useNetworkStore((s) => s.updateSignalingServer);
  const error = useNetworkStore((s) => s.error);

  const [serverUrl, setServerUrl] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Sync local state with store
  useEffect(() => {
    setServerUrl(signalingServer);
  }, [signalingServer]);

  const handleSave = async () => {
    if (serverUrl === signalingServer) return;

    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await updateSignalingServer(serverUrl);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } finally {
      setIsSaving(false);
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionState) {
      case 'connected':
        return 'text-green-500';
      case 'connecting':
      case 'authenticating':
        return 'text-yellow-500';
      case 'disconnected':
      default:
        return 'text-red-500';
    }
  };

  const getConnectionStatusLabel = () => {
    switch (connectionState) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'authenticating':
        return 'Authenticating...';
      case 'disconnected':
      default:
        return 'Disconnected';
    }
  };

  return (
    <section className="bg-cosmic-surface border border-cosmic-border rounded-lg p-4">
      <h3 className="text-lg font-medium mb-4">Network</h3>

      {/* Connection Status */}
      <div className="mb-4">
        <label className="block text-sm text-cosmic-muted mb-1">Connection Status</label>
        <div className="flex items-center gap-2">
          <span className={`font-medium ${getConnectionStatusColor()}`}>
            {getConnectionStatusLabel()}
          </span>
        </div>
      </div>

      {/* Signaling Server URL */}
      <div className="mb-4">
        <label className="block text-sm text-cosmic-muted mb-1">
          Signaling Server URL
        </label>
        <input
          type="text"
          value={serverUrl}
          onChange={(e) => setServerUrl(e.target.value)}
          placeholder="wss://signaling.example.com"
          className="w-full px-3 py-2 bg-cosmic-bg border border-cosmic-border rounded-md text-cosmic-text placeholder:text-cosmic-muted focus:outline-none focus:ring-2 focus:ring-cosmic-accent"
        />
        <p className="text-xs text-cosmic-muted mt-1">
          WebSocket URL of the signaling server for P2P connection establishment
        </p>
      </div>

      {/* Save Button */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={isSaving || serverUrl === signalingServer}
          className="px-4 py-2 bg-cosmic-accent text-white rounded-md hover:bg-cosmic-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSaving ? 'Saving...' : 'Save'}
        </button>
        {saveSuccess && (
          <span className="text-sm text-green-500">Saved successfully!</span>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-md">
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}
    </section>
  );
}
