/**
 * Type-safe PyWebView API client.
 *
 * CRITICAL: Use waitForPyWebView() before calling any API methods.
 * The pywebview.api object is injected asynchronously and may not
 * exist when window.onload fires.
 */

// Connection and presence types
export type ConnectionState = 'disconnected' | 'connecting' | 'authenticating' | 'connected';
export type UserStatus = 'online' | 'away' | 'busy' | 'invisible' | 'offline' | 'unknown';
export type P2PConnectionState = 'new' | 'connecting' | 'connected' | 'disconnected' | 'failed' | 'closed';

// Type definitions for Python API methods
export interface PyWebViewAPI {
  // Identity
  get_identity(): Promise<IdentityResponse | null>;
  generate_identity(display_name: string): Promise<IdentityResponse>;
  update_display_name(name: string): Promise<void>;

  // Backup
  export_backup(password: string): Promise<BackupResponse>;
  import_backup(backup_json: string, password: string): Promise<IdentityResponse>;

  // Contacts
  get_contacts(): Promise<ContactResponse[]>;
  add_contact(public_key: string, display_name: string): Promise<ContactResponse>;
  remove_contact(id: number): Promise<void>;
  set_contact_verified(id: number, verified: boolean): Promise<void>;

  // Network
  get_connection_state(): Promise<ConnectionState>;
  get_signaling_server(): Promise<string>;
  set_signaling_server(url: string): Promise<void>;
  get_user_status(): Promise<UserStatus>;
  set_user_status(status: UserStatus): Promise<void>;

  // Messaging
  initiate_p2p_connection(contact_id: number): Promise<void>;
  send_message(contact_id: number, body: string, reply_to?: string): Promise<MessageResponse | null>;
  get_messages(contact_id: number, limit?: number, before?: number): Promise<MessageResponse[]>;
  get_p2p_state(contact_id: number): Promise<P2PConnectionState>;
  send_typing(contact_id: number, active?: boolean): Promise<void>;
  edit_message(contact_id: number, message_id: string, new_body: string): Promise<ApiResult>;
  delete_message(contact_id: number, message_id: string): Promise<ApiResult>;
  add_reaction(contact_id: number, message_id: string, emoji: string): Promise<ApiResult>;
  remove_reaction(contact_id: number, message_id: string, emoji: string): Promise<ApiResult>;
  get_reactions(message_id: string): Promise<ReactionResponse[]>;

  // File Transfer
  send_file(contact_id: number, file_path: string): Promise<FileTransferResult>;
  cancel_transfer(contact_id: number, transfer_id: string, direction?: string): Promise<ApiResult>;
  resume_transfer(contact_id: number, transfer_id: string, file_path: string): Promise<FileTransferResult>;
  get_transfers(contact_id: number): Promise<FileTransfersList>;
  get_file(file_id: string): Promise<FileData>;
  get_file_preview(file_id: number): Promise<FilePreviewResponse>;
  open_file_dialog(): Promise<FileDialogResult>;

  // Voice Calls
  start_call(contact_id: number): Promise<CallResult>;
  accept_call(): Promise<ApiResult>;
  reject_call(): Promise<ApiResult>;
  end_call(): Promise<ApiResult>;
  set_muted(muted: boolean): Promise<void>;
  is_muted(): Promise<boolean>;
  get_call_state(): Promise<CallState | null>;

  // Voice Messages
  start_voice_recording(): Promise<VoiceRecordingResult>;
  stop_voice_recording(): Promise<VoiceRecordingResult>;
  cancel_voice_recording(): Promise<ApiResult>;
  get_recording_duration(): Promise<number>;
  get_audio_devices(): Promise<{ inputs: AudioDevice[]; outputs: AudioDevice[]; error?: string }>;
  set_audio_devices(input_id: number | null, output_id: number | null): Promise<void>;

  // System
  ping(): Promise<string>;
}

export interface IdentityResponse {
  publicKey: string;
  fingerprint: string;
  fingerprintFormatted: string;
  displayName: string;
}

export interface BackupResponse {
  backup: string;
}

export interface ContactResponse {
  id: number;
  publicKey: string;
  fingerprint: string;
  fingerprintFormatted: string;
  displayName: string;
  verified: boolean;
  addedAt: string;
  onlineStatus: UserStatus;
}

export interface MessageResponse {
  id: string;
  conversationId: number;
  senderId: string;
  type: 'text' | 'edit' | 'delete' | 'file';
  body: string | null;
  replyTo: string | null;
  edited: boolean;
  deleted: boolean;
  timestamp: number;
  receivedAt: number | null;
  fileId?: number | null;
}

export interface ApiResult {
  success: boolean;
  error?: string;
}

export interface ReactionResponse {
  id: number;
  messageId: string;
  senderId: string;
  emoji: string;
  timestamp: number;
}

// Voice call types
export type VoiceCallState = 'idle' | 'ringing_outgoing' | 'ringing_incoming' | 'connecting' | 'active' | 'reconnecting' | 'ended';

export interface CallState {
  callId: string;
  contactId: number;
  state: VoiceCallState;
  direction: 'outgoing' | 'incoming';
  muted: boolean;
  duration: number | null;
}

export interface AudioDevice {
  id: number;
  name: string;
  channels: number;
}

export interface CallResult {
  callId?: string;
  error?: string;
}

export interface VoiceRecordingResult {
  recordingPath?: string;
  id?: string;
  duration?: number;
  path?: string;
  error?: string;
}

// File Transfer types
export type TransferState = 'pending' | 'active' | 'paused' | 'complete' | 'cancelled' | 'failed';
export type TransferDirection = 'send' | 'receive';

export interface FileMetadata {
  id: string;
  filename: string;
  size: number;
  mimeType: string;
  transferId?: string;
}

export interface FileTransferProgress {
  transferId: string;
  bytesTransferred: number;
  totalBytes: number;
  state: TransferState;
  speedBps: number;
  etaSeconds: number;
}

export interface FileTransferResult {
  transferId?: string;
  error?: string;
}

export interface ResumableTransfer {
  id: string;
  contact_id: number;
  direction: TransferDirection;
  filename: string;
  size: number;
  bytes_transferred: number;
  state: TransferState;
  created_at: number;
}

export interface FileTransfersList {
  active: FileTransferProgress[];
  resumable: ResumableTransfer[];
  error?: string;
}

export interface FileData {
  id?: string;
  filename?: string;
  mimeType?: string;
  size?: number;
  data?: string; // base64 encoded
  error?: string;
}

export interface FileDialogResult {
  path?: string;
  name?: string;
  size?: number;
  cancelled?: boolean;
  error?: string;
}

export interface FilePreviewResponse {
  preview?: string;  // Base64-encoded JPEG
  mimeType?: string;
  error?: string;
}

// Event payload types for incoming messages
export interface MessageEventPayload {
  contactId: number;
  message: MessageResponse | EditEventData | DeleteEventData | ReactionEventData | TypingEventData;
}

export interface EditEventData {
  type: 'edit';
  targetId: string;
  newBody: string;
  timestamp: number;
}

export interface DeleteEventData {
  type: 'delete';
  targetId: string;
  timestamp: number;
}

export interface ReactionEventData {
  type: 'reaction';
  targetId: string;
  emoji: string;
  action: 'add' | 'remove';
  senderId: string;
}

export interface TypingEventData {
  type: 'typing';
  active: boolean;
}

export interface P2PStateEventPayload {
  contactId: number;
  state: P2PConnectionState;
}

export interface FileProgressEventPayload {
  contactId: number;
  progress: FileTransferProgress;
}

export interface FileReceivedEventPayload {
  contactId: number;
  file: FileMetadata;
}

export interface TransferCompleteEventPayload {
  contactId: number;
  transferId: string;
}

export interface TransferErrorEventPayload {
  contactId: number;
  transferId: string;
  error: string;
}

// Voice call event payloads
export interface CallStateEventPayload {
  contactId: number;
  state: VoiceCallState;
}

export interface IncomingCallEventPayload {
  callId: string;
  fromKey: string;
}

export interface CallEndedEventPayload {
  callId: string;
  reason: string;
}

export interface RemoteMuteEventPayload {
  callId: string;
  muted: boolean;
}

// Custom events dispatched by Python backend
declare global {
  interface Window {
    pywebview?: {
      api: PyWebViewAPI;
    };
  }

  interface WindowEventMap {
    'discordopus:connection': CustomEvent<{ state: ConnectionState }>;
    'discordopus:presence': CustomEvent<{ publicKey: string; status: UserStatus }>;
    'discordopus:message': CustomEvent<MessageEventPayload>;
    'discordopus:p2p_state': CustomEvent<P2PStateEventPayload>;
    'discordopus:file_progress': CustomEvent<FileProgressEventPayload>;
    'discordopus:file_received': CustomEvent<FileReceivedEventPayload>;
    'discordopus:transfer_complete': CustomEvent<TransferCompleteEventPayload>;
    'discordopus:transfer_error': CustomEvent<TransferErrorEventPayload>;
    'discordopus:call_state': CustomEvent<CallStateEventPayload>;
    'discordopus:incoming_call': CustomEvent<IncomingCallEventPayload>;
    'discordopus:call_answered': CustomEvent<{ callId: string }>;
    'discordopus:call_rejected': CustomEvent<CallEndedEventPayload>;
    'discordopus:call_ended': CustomEvent<CallEndedEventPayload>;
    'discordopus:remote_mute': CustomEvent<RemoteMuteEventPayload>;
  }
}

// Promise that resolves when PyWebView is ready
let pywebviewReadyPromise: Promise<void> | null = null;

/**
 * Wait for PyWebView API to be available.
 * Call this before using the api object.
 */
export function waitForPyWebView(): Promise<void> {
  if (pywebviewReadyPromise) {
    return pywebviewReadyPromise;
  }

  pywebviewReadyPromise = new Promise((resolve) => {
    if (window.pywebview?.api) {
      // Already available
      resolve();
      return;
    }

    // Wait for pywebviewready event
    window.addEventListener('pywebviewready', () => {
      resolve();
    });
  });

  return pywebviewReadyPromise;
}

/**
 * Get the PyWebView API.
 * MUST call waitForPyWebView() first.
 */
export function getApi(): PyWebViewAPI {
  if (!window.pywebview?.api) {
    throw new Error(
      'PyWebView API not available. Call waitForPyWebView() first.'
    );
  }
  return window.pywebview.api;
}

// Convenience export
export const api = {
  /**
   * Call an API method safely.
   * Waits for PyWebView and handles errors.
   */
  async call<T>(method: (api: PyWebViewAPI) => Promise<T>): Promise<T> {
    await waitForPyWebView();
    return method(getApi());
  },
};
