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
  reconnect(): Promise<ApiResult>;

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

  // Video Calls
  enable_video(source: 'camera' | 'screen'): Promise<VideoResult>;
  disable_video(): Promise<ApiResult>;
  set_camera(device_id: number): Promise<ApiResult>;
  set_screen_monitor(monitor_index: number): Promise<ApiResult>;
  get_video_state(): Promise<VideoState>;
  get_cameras(): Promise<CamerasResult>;
  get_monitors(): Promise<MonitorsResult>;
  get_local_video_frame(): Promise<VideoFrameResult>;
  get_remote_video_frame(): Promise<VideoFrameResult>;

  // Voice Messages
  start_voice_recording(): Promise<VoiceRecordingResult>;
  stop_voice_recording(): Promise<VoiceRecordingResult>;
  cancel_voice_recording(): Promise<ApiResult>;
  get_recording_duration(): Promise<number>;
  get_audio_devices(): Promise<{ inputs: AudioDevice[]; outputs: AudioDevice[]; error?: string }>;
  set_audio_devices(input_id: number | null, output_id: number | null): Promise<void>;

  // Groups
  create_group(name: string): Promise<Group>;
  get_groups(): Promise<Group[]>;
  get_group(group_id: string): Promise<Group | null>;
  generate_group_invite(group_id: string): Promise<string>;
  join_group(invite_code: string): Promise<Group>;
  leave_group(group_id: string): Promise<boolean>;
  get_group_members(group_id: string): Promise<GroupMember[]>;
  remove_group_member(group_id: string, public_key: string): Promise<boolean>;
  send_group_message(group_id: string, message_id: string, text: string): Promise<GroupMessage>;
  start_group_call(group_id: string, call_id: string): Promise<GroupCallStatus>;
  join_group_call(group_id: string, call_id: string): Promise<GroupCallStatus>;
  leave_group_call(group_id: string): Promise<boolean>;
  set_group_call_muted(group_id: string, muted: boolean): Promise<boolean>;
  get_group_call_bandwidth(participant_count: number): Promise<BandwidthEstimate>;

  // Update
  get_app_version(): Promise<string>;
  check_for_updates(): Promise<UpdateInfo | null>;
  download_update(): Promise<UpdateResult>;
  get_update_status(): Promise<UpdateStatus>;

  // Notification Settings
  get_notification_settings(): Promise<NotificationSettings>;
  set_notification_enabled(enabled: boolean): Promise<void>;
  set_notification_messages(enabled: boolean): Promise<void>;
  set_notification_calls(enabled: boolean): Promise<void>;

  // System
  ping(): Promise<string>;
  factory_reset(): Promise<FactoryResetResult>;

  // Discovery
  is_discovery_enabled(): Promise<boolean>;
  set_discovery_enabled(enabled: boolean): Promise<ApiResult>;
  get_discovered_users(): Promise<DiscoveredUser[]>;
}

export interface FactoryResetResult {
  success: boolean;
  message?: string;
  error?: string;
}

export interface DiscoveredUser {
  publicKey: string;
  displayName: string;
  status: UserStatus;
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

// Video call types
export type VideoSource = 'camera' | 'screen' | null;

export interface VideoState {
  videoEnabled: boolean;
  videoSource: VideoSource;
  remoteVideo: boolean;
}

export interface Camera {
  index: number;
  name: string;
  backend: number;
  path: string;
}

export interface Monitor {
  index: number;
  width: number;
  height: number;
  left: number;
  top: number;
}

export interface VideoResult {
  success?: boolean;
  source?: string;
  error?: string;
}

export interface CamerasResult {
  cameras: Camera[];
  error?: string;
}

export interface MonitorsResult {
  monitors: Monitor[];
  error?: string;
}

export interface VideoFrameResult {
  frame?: string | null;  // Base64-encoded JPEG
  error?: string;
}

export interface VoiceRecordingResult {
  recordingPath?: string;
  id?: string;
  duration?: number;
  path?: string;
  error?: string;
}

// Group types
export interface Group {
  id: string;
  name: string;
  creator_public_key: string;
  created_at: number;
  updated_at: number;
  invite_code: string | null;
  is_active: boolean;
}

export interface GroupMember {
  id: number | null;
  group_id: string;
  public_key: string;
  display_name: string;
  joined_at: number;
  is_admin: boolean;
}

export interface GroupMessage {
  type: string;
  group_id: string;
  message_id: string;
  sender_public_key: string;
  timestamp: number;
  message_index: number;
  ciphertext: string;
  signature: string;
}

export interface GroupCallStatus {
  group_id: string;
  call_id: string;
  status: string;
}

export interface BandwidthEstimate {
  upload_kbps: number;
  download_kbps: number;
  total_kbps: number;
  participant_count: number;
  warning: boolean;
  message: string | null;
}

// Update types
export interface UpdateInfo {
  version: string;
  changelog: string;
  size_bytes?: number;
  is_patch?: boolean;
}

export interface UpdateResult {
  success: boolean;
  message?: string;
  error?: string;
}

export interface UpdateStatus {
  currentVersion: string;
  updateAvailable: boolean;
  availableUpdate: UpdateInfo | null;
  error?: string;
}

// Notification Settings types
export interface NotificationSettings {
  enabled: boolean;
  messages: boolean;
  calls: boolean;
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

// Video event payloads
// veilcord:video_state - Fired when local video state changes
export interface VideoStateEventPayload {
  videoEnabled: boolean;
  videoSource: VideoSource;
  remoteVideo: boolean;
}

// veilcord:remote_video_changed - Fired when remote party enables/disables video
export interface RemoteVideoEventPayload {
  hasVideo: boolean;
}

// Group event payloads
export interface GroupCreatedEventPayload {
  group: Group;
}

export interface GroupJoinedEventPayload {
  group: Group;
}

export interface GroupLeftEventPayload {
  group_id: string;
}

export interface GroupMemberAddedEventPayload {
  group_id: string;
  member: GroupMember;
}

export interface GroupMemberRemovedEventPayload {
  group_id: string;
  public_key: string;
}

export interface GroupCallStateEventPayload {
  group_id: string;
  state: string;
}

export interface GroupMessageEventPayload {
  group_id: string;
  message: {
    message_id: string;
    sender_public_key: string;
    body: string;
    timestamp: number;
  };
}

// Update event payloads
export interface UpdateAvailableEventPayload {
  version: string;
}

// Notification event payloads
export interface OpenChatEventPayload {
  contactId: number;
}

// Discovery event payloads
export interface DiscoveryUserEventPayload {
  action: 'join' | 'leave';
  publicKey: string;
  displayName?: string;
  status?: UserStatus;
}

// Custom events dispatched by Python backend
declare global {
  interface Window {
    pywebview?: {
      api: PyWebViewAPI;
    };
  }

  interface WindowEventMap {
    'veilcord:connection': CustomEvent<{ state: ConnectionState }>;
    'veilcord:presence': CustomEvent<{ publicKey: string; status: UserStatus }>;
    'veilcord:message': CustomEvent<MessageEventPayload>;
    'veilcord:p2p_state': CustomEvent<P2PStateEventPayload>;
    'veilcord:file_progress': CustomEvent<FileProgressEventPayload>;
    'veilcord:file_received': CustomEvent<FileReceivedEventPayload>;
    'veilcord:transfer_complete': CustomEvent<TransferCompleteEventPayload>;
    'veilcord:transfer_error': CustomEvent<TransferErrorEventPayload>;
    'veilcord:call_state': CustomEvent<CallStateEventPayload>;
    'veilcord:incoming_call': CustomEvent<IncomingCallEventPayload>;
    'veilcord:call_answered': CustomEvent<{ callId: string }>;
    'veilcord:call_rejected': CustomEvent<CallEndedEventPayload>;
    'veilcord:call_ended': CustomEvent<CallEndedEventPayload>;
    'veilcord:remote_mute': CustomEvent<RemoteMuteEventPayload>;
    'veilcord:video_state': CustomEvent<VideoStateEventPayload>;
    'veilcord:remote_video_changed': CustomEvent<RemoteVideoEventPayload>;
    'veilcord:group_created': CustomEvent<GroupCreatedEventPayload>;
    'veilcord:group_joined': CustomEvent<GroupJoinedEventPayload>;
    'veilcord:group_left': CustomEvent<GroupLeftEventPayload>;
    'veilcord:group_member_added': CustomEvent<GroupMemberAddedEventPayload>;
    'veilcord:group_member_removed': CustomEvent<GroupMemberRemovedEventPayload>;
    'veilcord:group_call_state': CustomEvent<GroupCallStateEventPayload>;
    'veilcord:group_message': CustomEvent<GroupMessageEventPayload>;
    'veilcord:update_available': CustomEvent<UpdateAvailableEventPayload>;
    'veilcord:open_chat': CustomEvent<OpenChatEventPayload>;
    'veilcord:discovery_user': CustomEvent<DiscoveryUserEventPayload>;
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
