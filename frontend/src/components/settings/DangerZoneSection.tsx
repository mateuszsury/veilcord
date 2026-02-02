/**
 * Danger Zone section for destructive operations like factory reset.
 *
 * Includes multiple confirmation steps to prevent accidental data loss.
 */

import { useState } from 'react';
import { api } from '@/lib/pywebview';
import { Button } from '@/components/ui/Button';
import { AlertTriangle, Check, Trash2 } from 'lucide-react';

export function DangerZoneSection() {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [isResetting, setIsResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const CONFIRM_PHRASE = 'RESET';

  const handleReset = async () => {
    if (confirmText !== CONFIRM_PHRASE) return;

    setIsResetting(true);
    setError(null);

    try {
      const result = await api.call((a) => a.factory_reset());
      if (result.success) {
        setSuccess(true);
        // App needs restart - show message
      } else {
        setError(result.error || 'Factory reset failed');
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setIsResetting(false);
    }
  };

  const handleClose = () => {
    setShowConfirmDialog(false);
    setConfirmText('');
    setError(null);
  };

  if (success) {
    return (
      <section className="space-y-6">
        <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
          <AlertTriangle size={20} className="text-status-busy" />
          Danger Zone
        </h3>
        <div className="h-px bg-discord-bg-tertiary" />
        <div className="bg-status-online/10 border border-status-online/30 rounded-lg p-4 text-center">
          <Check className="w-12 h-12 mx-auto mb-2 text-status-online" />
          <p className="text-status-online font-medium">Factory reset complete!</p>
          <p className="text-discord-text-muted text-sm mt-2">Please close and restart the application.</p>
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="space-y-6">
        <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
          <AlertTriangle size={20} className="text-status-busy" />
          Danger Zone
        </h3>

        <div className="h-px bg-status-busy/30" />

        <div className="bg-status-busy/10 border border-status-busy/30 rounded-lg p-4">
          <p className="text-discord-text-muted text-sm mb-4">
            Irreversible actions that will permanently delete your data.
          </p>

          <div className="flex items-start gap-4">
            <div className="flex-1">
              <h4 className="text-discord-text-primary font-medium flex items-center gap-2">
                <Trash2 size={16} className="text-status-busy" />
                Factory Reset
              </h4>
              <p className="text-discord-text-muted text-sm mt-1">
                Delete all data including your identity, contacts, messages, files, and settings.
                This action cannot be undone.
              </p>
            </div>
            <Button
              variant="danger"
              onClick={() => setShowConfirmDialog(true)}
            >
              Reset All Data
            </Button>
          </div>
        </div>
      </section>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-discord-bg-secondary rounded-lg p-6 w-[420px] max-w-[90vw] border border-status-busy/50 shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-status-busy/20 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-status-busy" />
              </div>
              <h2 className="text-xl font-semibold text-status-busy">Factory Reset</h2>
            </div>

            <div className="mb-4 text-discord-text-primary">
              <p className="mb-3">This will permanently delete:</p>
              <ul className="list-disc list-inside text-discord-text-muted space-y-1 ml-2">
                <li>Your cryptographic identity (keys)</li>
                <li>All contacts</li>
                <li>All messages and chat history</li>
                <li>All transferred files</li>
                <li>All voice messages</li>
                <li>All settings</li>
              </ul>
            </div>

            <div className="bg-status-busy/10 border border-status-busy/30 rounded p-3 mb-4">
              <p className="text-status-busy text-sm font-medium">
                This action is irreversible. Make sure you have exported a backup if you want to keep your identity.
              </p>
            </div>

            <div className="mb-4">
              <label className="block text-sm text-discord-text-muted mb-2">
                Type <span className="font-mono font-bold text-status-busy">{CONFIRM_PHRASE}</span> to confirm:
              </label>
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value.toUpperCase())}
                placeholder={CONFIRM_PHRASE}
                className="
                  w-full bg-discord-bg-tertiary border border-discord-bg-modifier-active
                  rounded-md px-3 py-2 text-discord-text-primary
                  placeholder:text-discord-text-muted
                  focus:ring-2 focus:ring-status-busy focus:border-transparent
                  focus:outline-none
                  disabled:opacity-50 disabled:cursor-not-allowed
                "
                autoFocus
                disabled={isResetting}
              />
            </div>

            {error && (
              <p className="text-status-busy text-sm mb-4">{error}</p>
            )}

            <div className="flex gap-2 justify-end">
              <Button
                variant="ghost"
                onClick={handleClose}
                disabled={isResetting}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleReset}
                disabled={isResetting || confirmText !== CONFIRM_PHRASE}
              >
                {isResetting ? 'Resetting...' : 'Delete Everything'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
