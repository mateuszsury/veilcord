/**
 * Key backup settings section.
 *
 * Allows users to export and import encrypted identity backups.
 */

import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { api } from '@/lib/pywebview';
import { useIdentityStore } from '@/stores/identity';
import { Button } from '@/components/ui/Button';
import { Download, Upload, Key } from 'lucide-react';

export function BackupSection() {
  const identity = useIdentityStore((s) => s.identity);
  const setIdentity = useIdentityStore((s) => s.setIdentity);
  const [exportPassword, setExportPassword] = useState('');
  const [importPassword, setImportPassword] = useState('');
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleExport = async () => {
    if (exportPassword.length < 4) {
      setStatus({ type: 'error', message: 'Password must be at least 4 characters' });
      return;
    }

    try {
      const result = await api.call((a) => a.export_backup(exportPassword));

      // Download as file
      const blob = new Blob([result.backup], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `discordopus-backup-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);

      setStatus({ type: 'success', message: 'Backup exported successfully' });
      setExportPassword('');
    } catch (err) {
      setStatus({ type: 'error', message: err instanceof Error ? err.message : 'Export failed' });
    }
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (importPassword.length < 4) {
      setStatus({ type: 'error', message: 'Enter the backup password first' });
      return;
    }

    try {
      const text = await file.text();
      const newIdentity = await api.call((a) => a.import_backup(text, importPassword));
      setIdentity(newIdentity);
      setStatus({ type: 'success', message: 'Identity restored successfully' });
      setImportPassword('');
    } catch (err) {
      setStatus({ type: 'error', message: err instanceof Error ? err.message : 'Import failed' });
    }

    // Reset file input
    e.target.value = '';
  };

  if (!identity) {
    return (
      <section className="space-y-6">
        <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
          <Key size={20} />
          Key Backup
        </h3>
        <div className="h-px bg-discord-bg-tertiary" />
        <p className="text-sm text-discord-text-muted">
          Generate an identity first to enable backup.
        </p>
      </section>
    );
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <h3 className="text-lg font-semibold text-discord-text-primary flex items-center gap-2">
        <Key size={20} />
        Key Backup
      </h3>

      <div className="h-px bg-discord-bg-tertiary" />

      <p className="text-sm text-discord-text-muted">
        Create a password-protected backup of your identity keys. Store it safely -
        you'll need it to recover your identity if you reinstall Windows.
      </p>

      {status && (
        <div
          className={`p-3 rounded-md text-sm ${
            status.type === 'success'
              ? 'bg-status-online/10 text-status-online border border-status-online/30'
              : 'bg-status-busy/10 text-status-busy border border-status-busy/30'
          }`}
        >
          {status.message}
        </div>
      )}

      <div className="space-y-4">
        {/* Export */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-discord-text-primary flex items-center gap-2">
            <Download size={14} />
            Export Backup
          </label>
          <div className="flex gap-2">
            <input
              type="password"
              value={exportPassword}
              onChange={(e) => setExportPassword(e.target.value)}
              placeholder="Create backup password"
              className="
                flex-1 bg-discord-bg-tertiary border border-discord-bg-modifier-active
                rounded-md px-3 py-2 text-discord-text-primary
                placeholder:text-discord-text-muted
                focus:ring-2 focus:ring-accent-red focus:border-transparent
                focus:outline-none
              "
            />
            <Button onClick={handleExport}>
              Export
            </Button>
          </div>
        </div>

        {/* Import */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-discord-text-primary flex items-center gap-2">
            <Upload size={14} />
            Import Backup
          </label>
          <div className="flex gap-2">
            <input
              type="password"
              value={importPassword}
              onChange={(e) => setImportPassword(e.target.value)}
              placeholder="Enter backup password"
              className="
                flex-1 bg-discord-bg-tertiary border border-discord-bg-modifier-active
                rounded-md px-3 py-2 text-discord-text-primary
                placeholder:text-discord-text-muted
                focus:ring-2 focus:ring-accent-red focus:border-transparent
                focus:outline-none
              "
            />
            <Button onClick={handleImportClick} variant="secondary">
              Import
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        </div>
      </div>
    </motion.section>
  );
}
