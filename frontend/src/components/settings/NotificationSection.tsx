/**
 * Notification settings section.
 *
 * Controls Windows notification preferences:
 * - Global enable/disable
 * - Message notifications toggle
 * - Call notifications toggle
 */

import { useState, useEffect } from 'react';
import { api } from '@/lib/pywebview';
import { Bell, MessageSquare, Phone, Info } from 'lucide-react';
import type { NotificationSettings } from '@/lib/pywebview';

export function NotificationSection() {
  const [settings, setSettings] = useState<NotificationSettings>({
    enabled: true,
    messages: true,
    calls: true,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      const result = await api.call((a) => a.get_notification_settings());
      if (result) {
        setSettings(result);
      }
    } catch (error) {
      console.error('Failed to load notification settings:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleEnabledChange(enabled: boolean) {
    try {
      await api.call((a) => a.set_notification_enabled(enabled));
      setSettings(prev => ({ ...prev, enabled }));
    } catch (error) {
      console.error('Failed to update notification enabled:', error);
    }
  }

  async function handleMessagesChange(messages: boolean) {
    try {
      await api.call((a) => a.set_notification_messages(messages));
      setSettings(prev => ({ ...prev, messages }));
    } catch (error) {
      console.error('Failed to update message notifications:', error);
    }
  }

  async function handleCallsChange(calls: boolean) {
    try {
      await api.call((a) => a.set_notification_calls(calls));
      setSettings(prev => ({ ...prev, calls }));
    } catch (error) {
      console.error('Failed to update call notifications:', error);
    }
  }

  if (loading) {
    return (
      <section className="space-y-6">
        <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
          <Bell size={20} />
          Notifications
        </h3>
        <div className="h-px bg-discord-bg-tertiary" />
        <p className="text-sm text-discord-text-muted">Loading settings...</p>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
        <Bell size={20} />
        Notifications
      </h3>

      <div className="h-px bg-discord-bg-tertiary" />

      <div className="space-y-4">
        {/* Global enable/disable */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary">
              Enable Notifications
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              Show Windows notifications when app is in background
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={settings.enabled}
              onChange={(e) => handleEnabledChange(e.target.checked)}
            />
            <div className="
              w-11 h-6 bg-discord-bg-modifier-active rounded-full peer
              peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-accent-red
              peer-checked:after:translate-x-full peer-checked:after:border-white
              after:content-[''] after:absolute after:top-[2px] after:left-[2px]
              after:bg-white after:border-gray-300 after:border after:rounded-full
              after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-red
            "></div>
          </label>
        </div>

        {/* Message notifications */}
        <div className={`flex items-start justify-between gap-4 ${!settings.enabled ? 'opacity-50' : ''}`}>
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary flex items-center gap-2">
              <MessageSquare size={14} />
              Message Notifications
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              Notify when new messages arrive
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={settings.messages}
              disabled={!settings.enabled}
              onChange={(e) => handleMessagesChange(e.target.checked)}
            />
            <div className="
              w-11 h-6 bg-discord-bg-modifier-active rounded-full peer
              peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-accent-red
              peer-checked:after:translate-x-full peer-checked:after:border-white
              after:content-[''] after:absolute after:top-[2px] after:left-[2px]
              after:bg-white after:border-gray-300 after:border after:rounded-full
              after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-red
              peer-disabled:cursor-not-allowed
            "></div>
          </label>
        </div>

        {/* Call notifications */}
        <div className={`flex items-start justify-between gap-4 ${!settings.enabled ? 'opacity-50' : ''}`}>
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary flex items-center gap-2">
              <Phone size={14} />
              Call Notifications
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              Notify for incoming calls with accept/reject buttons
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={settings.calls}
              disabled={!settings.enabled}
              onChange={(e) => handleCallsChange(e.target.checked)}
            />
            <div className="
              w-11 h-6 bg-discord-bg-modifier-active rounded-full peer
              peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-accent-red
              peer-checked:after:translate-x-full peer-checked:after:border-white
              after:content-[''] after:absolute after:top-[2px] after:left-[2px]
              after:bg-white after:border-gray-300 after:border after:rounded-full
              after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-red
              peer-disabled:cursor-not-allowed
            "></div>
          </label>
        </div>

        {/* Info note */}
        <div className="mt-4 p-3 bg-discord-bg-tertiary rounded-lg border border-discord-bg-modifier-active">
          <p className="text-sm text-discord-text-muted flex items-center gap-2">
            <Info size={14} className="text-accent-red-text" />
            Notifications respect Windows Do Not Disturb mode automatically.
          </p>
        </div>
      </div>
    </section>
  );
}
