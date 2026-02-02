/**
 * Network settings section.
 *
 * Displays connection status and signaling server configuration.
 */

import { useState, useEffect } from 'react';
import { useNetworkStore } from '@/stores/network';
import { Button } from '@/components/ui/Button';
import { Wifi, RefreshCw } from 'lucide-react';

export function NetworkSection() {
  const signalingServer = useNetworkStore((s) => s.signalingServer);
  const connectionState = useNetworkStore((s) => s.connectionState);
  const updateSignalingServer = useNetworkStore((s) => s.updateSignalingServer);
  const reconnect = useNetworkStore((s) => s.reconnect);
  const error = useNetworkStore((s) => s.error);

  const [serverUrl, setServerUrl] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

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

  const handleReconnect = async () => {
    setIsReconnecting(true);
    try {
      await reconnect();
    } finally {
      setIsReconnecting(false);
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionState) {
      case 'connected':
        return 'text-status-online';
      case 'connecting':
      case 'authenticating':
        return 'text-status-away';
      case 'disconnected':
      default:
        return 'text-status-busy';
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
    <section className="space-y-6">
      <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
        <Wifi size={20} />
        Network
      </h3>

      <div className="h-px bg-discord-bg-tertiary" />

      <div className="space-y-4">
        {/* Connection Status */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary">
              Connection Status
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              Current connection to signaling server
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-sm font-medium ${getConnectionStatusColor()}`}>
              {getConnectionStatusLabel()}
            </span>
            <Button
              onClick={handleReconnect}
              disabled={isReconnecting || connectionState === 'connecting' || connectionState === 'authenticating'}
              variant="secondary"
              size="sm"
            >
              {isReconnecting ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  <span className="ml-1">Reconnecting...</span>
                </>
              ) : (
                'Reconnect'
              )}
            </Button>
          </div>
        </div>

        {/* Signaling Server URL */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary">
              Signaling Server URL
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              WebSocket URL for P2P connection establishment
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={serverUrl}
            onChange={(e) => setServerUrl(e.target.value)}
            placeholder="wss://signaling.example.com"
            className="
              flex-1 bg-discord-bg-tertiary border border-discord-bg-modifier-active
              rounded-md px-3 py-2 text-discord-text-primary
              placeholder:text-discord-text-muted
              focus:ring-2 focus:ring-accent-red focus:border-transparent
              focus:outline-none
            "
          />
          <Button
            onClick={handleSave}
            disabled={isSaving || serverUrl === signalingServer}
          >
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </div>

        {saveSuccess && (
          <p className="text-sm text-status-online">Saved successfully!</p>
        )}

        {/* Error Display */}
        {error && (
          <div className="p-3 bg-status-busy/10 border border-status-busy/30 rounded-md">
            <p className="text-sm text-status-busy">{error}</p>
          </div>
        )}
      </div>
    </section>
  );
}
