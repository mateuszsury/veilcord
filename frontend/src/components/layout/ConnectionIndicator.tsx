import { useNetworkStore } from '@/stores/network';
import type { ConnectionState } from '@/lib/pywebview';

function getConnectionInfo(state: ConnectionState): { label: string; color: string; icon: string } {
  switch (state) {
    case 'connected':
      return { label: 'Connected', color: 'text-green-500', icon: 'M5 12h14M12 5v14' };
    case 'connecting':
      return { label: 'Connecting...', color: 'text-yellow-500', icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' };
    case 'authenticating':
      return { label: 'Authenticating...', color: 'text-blue-500', icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' };
    case 'disconnected':
    default:
      return { label: 'Disconnected', color: 'text-red-500', icon: 'M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636' };
  }
}

export function ConnectionIndicator() {
  const connectionState = useNetworkStore((s) => s.connectionState);
  const signalingServer = useNetworkStore((s) => s.signalingServer);
  const { label, color, icon } = getConnectionInfo(connectionState);

  return (
    <div className="flex items-center gap-2 px-2 py-1" title={signalingServer || 'No server configured'}>
      <svg
        className={`w-4 h-4 ${color}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
      </svg>
      <span className={`text-xs ${color}`}>{label}</span>
    </div>
  );
}
