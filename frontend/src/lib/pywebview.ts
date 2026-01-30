/**
 * Type-safe PyWebView API client.
 *
 * CRITICAL: Use waitForPyWebView() before calling any API methods.
 * The pywebview.api object is injected asynchronously and may not
 * exist when window.onload fires.
 */

// Type definitions for Python API methods
export interface PyWebViewAPI {
  // Identity
  get_identity(): Promise<IdentityResponse | null>;
  generate_identity(display_name: string): Promise<IdentityResponse>;
  update_display_name(name: string): Promise<void>;

  // Backup
  export_backup(password: string): Promise<string>;
  import_backup(backup_json: string, password: string): Promise<IdentityResponse>;

  // Contacts
  get_contacts(): Promise<ContactResponse[]>;
  add_contact(public_key: string, display_name: string): Promise<ContactResponse>;
  remove_contact(id: number): Promise<void>;
  set_contact_verified(id: number, verified: boolean): Promise<void>;

  // System
  ping(): Promise<string>;
}

export interface IdentityResponse {
  publicKey: string;
  fingerprint: string;
  displayName: string;
}

export interface ContactResponse {
  id: number;
  publicKey: string;
  fingerprint: string;
  displayName: string;
  verified: boolean;
  addedAt: string;
}

// Declare global window type extension
declare global {
  interface Window {
    pywebview?: {
      api: PyWebViewAPI;
    };
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
