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
  type: 'text' | 'edit' | 'delete';
  body: string | null;
  replyTo: string | null;
  edited: boolean;
  deleted: boolean;
  timestamp: number;
  receivedAt: number | null;
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
