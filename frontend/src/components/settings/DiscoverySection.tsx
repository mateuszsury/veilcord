/**
 * Discovery settings section.
 *
 * Allows users to enable/disable autodiscovery with a warning
 * about visibility to other users.
 */

import { useState, useEffect } from 'react';
import { useDiscoveryStore } from '@/stores/discovery';
import { Button } from '@/components/ui/Button';
import { Eye, AlertTriangle } from 'lucide-react';

export function DiscoverySection() {
  const enabled = useDiscoveryStore((s) => s.enabled);
  const isLoading = useDiscoveryStore((s) => s.isLoading);
  const error = useDiscoveryStore((s) => s.error);
  const loadState = useDiscoveryStore((s) => s.loadState);
  const toggleDiscovery = useDiscoveryStore((s) => s.toggleDiscovery);

  const [isToggling, setIsToggling] = useState(false);
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    loadState();
  }, [loadState]);

  const handleToggle = async () => {
    if (!enabled) {
      // Show warning before enabling
      setShowWarning(true);
    } else {
      // Disable directly
      setIsToggling(true);
      await toggleDiscovery(false);
      setIsToggling(false);
    }
  };

  const handleConfirmEnable = async () => {
    setShowWarning(false);
    setIsToggling(true);
    await toggleDiscovery(true);
    setIsToggling(false);
  };

  const handleCancelEnable = () => {
    setShowWarning(false);
  };

  return (
    <section className="space-y-6">
      <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
        <Eye size={20} />
        Discovery
      </h3>

      <div className="h-px bg-discord-bg-tertiary" />

      <div className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary">
              Autodiscovery
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              {enabled
                ? 'You are visible to other discoverable users'
                : 'You are not visible to others'}
            </p>
          </div>
          <button
            onClick={handleToggle}
            disabled={isLoading || isToggling}
            className={`
              relative w-12 h-6 rounded-full transition-colors
              ${enabled ? 'bg-accent-red' : 'bg-discord-bg-modifier-active'}
              ${isLoading || isToggling ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <span
              className={`
                absolute top-1 w-4 h-4 rounded-full bg-white transition-transform
                ${enabled ? 'left-7' : 'left-1'}
              `}
            />
          </button>
        </div>

        {error && (
          <p className="text-sm text-status-busy">{error}</p>
        )}

        <p className="text-sm text-discord-text-muted">
          Make yourself visible to other users on the same server.
        </p>
      </div>

      {/* Warning Dialog */}
      {showWarning && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-discord-bg-secondary rounded-lg p-6 w-96 max-w-[90vw] border border-discord-bg-tertiary shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-status-away/20 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-status-away" />
              </div>
              <h2 className="text-xl font-semibold text-discord-text-primary">
                Enable Discovery?
              </h2>
            </div>

            <div className="mb-4 text-discord-text-primary">
              <p className="mb-3">When discovery is enabled:</p>
              <ul className="list-disc list-inside text-discord-text-muted space-y-1 ml-2">
                <li>Your display name will be visible to others</li>
                <li>Your online status will be visible</li>
                <li>Other users can see you in the Discovery tab</li>
                <li>Anyone on the same server can add you as a contact</li>
              </ul>
            </div>

            <div className="bg-status-away/10 border border-status-away/30 rounded p-3 mb-4">
              <p className="text-status-away text-sm">
                Only enable this if you trust all users on the signaling server.
              </p>
            </div>

            <div className="flex gap-2 justify-end">
              <Button
                onClick={handleCancelEnable}
                variant="ghost"
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmEnable}
              >
                Enable Discovery
              </Button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
