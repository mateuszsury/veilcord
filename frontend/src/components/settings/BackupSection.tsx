import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { api } from '@/lib/pywebview';
import { useIdentityStore } from '@/stores/identity';

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
      <div className="bg-cosmic-surface rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Key Backup</h3>
        <p className="text-cosmic-muted">Generate an identity first to enable backup.</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-cosmic-surface rounded-lg p-6"
    >
      <h3 className="text-lg font-semibold mb-4">Key Backup</h3>
      <p className="text-sm text-cosmic-muted mb-4">
        Create a password-protected backup of your identity keys. Store it safely -
        you'll need it to recover your identity if you reinstall Windows.
      </p>

      {status && (
        <div
          className={`mb-4 p-3 rounded-md text-sm ${
            status.type === 'success'
              ? 'bg-green-900/30 text-green-400'
              : 'bg-red-900/30 text-red-400'
          }`}
        >
          {status.message}
        </div>
      )}

      {/* Export */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Export Backup</label>
        <div className="flex gap-2">
          <input
            type="password"
            value={exportPassword}
            onChange={(e) => setExportPassword(e.target.value)}
            placeholder="Create backup password"
            className="flex-1 bg-cosmic-bg border border-cosmic-border rounded-md px-3 py-2 text-cosmic-text focus:outline-none focus:border-cosmic-accent"
          />
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-cosmic-accent hover:bg-cosmic-accent-hover text-white rounded-md"
          >
            Export
          </button>
        </div>
      </div>

      {/* Import */}
      <div>
        <label className="block text-sm font-medium mb-2">Import Backup</label>
        <div className="flex gap-2">
          <input
            type="password"
            value={importPassword}
            onChange={(e) => setImportPassword(e.target.value)}
            placeholder="Enter backup password"
            className="flex-1 bg-cosmic-bg border border-cosmic-border rounded-md px-3 py-2 text-cosmic-text focus:outline-none focus:border-cosmic-accent"
          />
          <button
            onClick={handleImportClick}
            className="px-4 py-2 bg-cosmic-border hover:bg-cosmic-muted/20 rounded-md"
          >
            Import
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>
      </div>
    </motion.div>
  );
}
