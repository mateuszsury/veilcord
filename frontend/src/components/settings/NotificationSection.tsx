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
      <div className="bg-gray-800/50 rounded-lg p-4">
        <h3 className="text-lg font-medium text-white mb-4">Notifications</h3>
        <p className="text-gray-400">Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 rounded-lg p-4">
      <h3 className="text-lg font-medium text-white mb-4">Notifications</h3>

      <div className="space-y-4">
        {/* Global enable/disable */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white">Enable Notifications</p>
            <p className="text-sm text-gray-400">
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
            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-purple-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
          </label>
        </div>

        {/* Message notifications */}
        <div className={`flex items-center justify-between ${!settings.enabled ? 'opacity-50' : ''}`}>
          <div>
            <p className="text-white">Message Notifications</p>
            <p className="text-sm text-gray-400">
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
            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-purple-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600 peer-disabled:cursor-not-allowed"></div>
          </label>
        </div>

        {/* Call notifications */}
        <div className={`flex items-center justify-between ${!settings.enabled ? 'opacity-50' : ''}`}>
          <div>
            <p className="text-white">Call Notifications</p>
            <p className="text-sm text-gray-400">
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
            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-purple-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600 peer-disabled:cursor-not-allowed"></div>
          </label>
        </div>

        {/* Info note */}
        <div className="mt-6 p-3 bg-gray-800/50 rounded-lg border border-gray-700">
          <p className="text-sm text-gray-400">
            <span className="text-purple-400">Note:</span> Notifications respect Windows Do Not Disturb mode automatically.
          </p>
        </div>
      </div>
    </div>
  );
}
