"""
Windows toast notification service using Windows-Toasts library.

Provides interactive notifications for messages and incoming calls with
action buttons that trigger callbacks to open relevant UI.

CRITICAL: Uses InteractableWindowsToaster (not WindowsToaster) to enable
action button callbacks after notifications are relegated to Action Center.

AUMID Registration:
For callbacks to work reliably, a custom AUMID should be registered. This is
handled automatically by using app_id parameter on first use. For production,
run the AUMID registration script during installation.
"""

import logging
from typing import Callable, Optional
from threading import Lock

from windows_toasts import InteractableWindowsToaster, Toast, ToastButton, ToastActivatedEventArgs

from src.storage.settings import get_setting, Settings

logger = logging.getLogger(__name__)

# Application User Model ID for notifications
AUMID = "DiscordOpus.SecureMessenger"


class NotificationService:
    """
    Windows toast notification service.

    Shows interactive notifications for messages and calls with
    action buttons. Respects user notification preferences.

    Usage:
        service = NotificationService()
        service.on_open_chat = lambda contact_id: switch_to_chat(contact_id)
        service.on_accept_call = lambda call_id: accept_call(call_id)
        service.show_message_notification("Alice", "Hello!", contact_id=123)
    """

    def __init__(self):
        """Initialize notification service."""
        self._toaster: Optional[InteractableWindowsToaster] = None
        self._lock = Lock()

        # Callbacks set by NetworkService
        self.on_open_chat: Optional[Callable[[int], None]] = None
        self.on_accept_call: Optional[Callable[[str], None]] = None
        self.on_reject_call: Optional[Callable[[str], None]] = None

    def _get_toaster(self) -> InteractableWindowsToaster:
        """Get or create toaster instance (lazy initialization)."""
        if self._toaster is None:
            with self._lock:
                if self._toaster is None:
                    try:
                        self._toaster = InteractableWindowsToaster(AUMID)
                        logger.info(f"Initialized InteractableWindowsToaster with AUMID: {AUMID}")
                    except Exception as e:
                        logger.error(f"Failed to initialize toaster: {e}")
                        raise
        return self._toaster

    def _is_enabled(self) -> bool:
        """Check if notifications are globally enabled."""
        enabled = get_setting(Settings.NOTIFICATIONS_ENABLED)
        return enabled == "true"

    def _messages_enabled(self) -> bool:
        """Check if message notifications are enabled."""
        if not self._is_enabled():
            return False
        enabled = get_setting(Settings.NOTIFICATIONS_MESSAGES)
        return enabled == "true"

    def _calls_enabled(self) -> bool:
        """Check if call notifications are enabled."""
        if not self._is_enabled():
            return False
        enabled = get_setting(Settings.NOTIFICATIONS_CALLS)
        return enabled == "true"

    def show_message_notification(
        self,
        sender_name: str,
        preview: str,
        contact_id: int
    ) -> None:
        """
        Show notification for new message.

        Args:
            sender_name: Display name of message sender
            preview: Message preview text (first ~100 chars)
            contact_id: Contact database ID for callback
        """
        if not self._messages_enabled():
            logger.debug("Message notifications disabled, skipping")
            return

        try:
            toaster = self._get_toaster()

            # Create toast with message preview
            toast = Toast([f"Message from {sender_name}", preview[:100]])

            # Add "Open" action button
            toast.AddAction(ToastButton("Open", f"open_chat:{contact_id}"))

            # Handle activation (click on toast or button)
            def on_activated(args: ToastActivatedEventArgs):
                arguments = args.arguments if args.arguments else ""
                logger.debug(f"Message notification activated: {arguments}")

                if arguments.startswith("open_chat:"):
                    try:
                        cid = int(arguments.split(":")[1])
                        if self.on_open_chat:
                            self.on_open_chat(cid)
                    except (ValueError, IndexError) as e:
                        logger.error(f"Failed to parse contact_id: {e}")
                elif self.on_open_chat:
                    # Clicked on toast body - also open chat
                    self.on_open_chat(contact_id)

            toast.on_activated = on_activated
            toaster.show_toast(toast)
            logger.debug(f"Showed message notification from {sender_name}")

        except Exception as e:
            logger.error(f"Failed to show message notification: {e}")

    def show_call_notification(
        self,
        caller_name: str,
        call_id: str,
        contact_id: int
    ) -> None:
        """
        Show notification for incoming call with Accept/Reject buttons.

        Args:
            caller_name: Display name of caller
            call_id: Call UUID for accept/reject callbacks
            contact_id: Contact database ID
        """
        if not self._calls_enabled():
            logger.debug("Call notifications disabled, skipping")
            return

        try:
            toaster = self._get_toaster()

            # Create toast for incoming call
            toast = Toast([f"Incoming call from {caller_name}", ""])

            # Add Accept and Reject action buttons
            toast.AddAction(ToastButton("Accept", f"accept_call:{call_id}"))
            toast.AddAction(ToastButton("Reject", f"reject_call:{call_id}"))

            def on_activated(args: ToastActivatedEventArgs):
                arguments = args.arguments if args.arguments else ""
                logger.debug(f"Call notification activated: {arguments}")

                if arguments.startswith("accept_call:"):
                    cid = arguments.split(":")[1]
                    if self.on_accept_call:
                        self.on_accept_call(cid)
                elif arguments.startswith("reject_call:"):
                    cid = arguments.split(":")[1]
                    if self.on_reject_call:
                        self.on_reject_call(cid)
                else:
                    # Clicked on toast body - bring app to focus but don't auto-accept
                    logger.debug("Call notification clicked (body)")

            toast.on_activated = on_activated
            toaster.show_toast(toast)
            logger.debug(f"Showed call notification from {caller_name}")

        except Exception as e:
            logger.error(f"Failed to show call notification: {e}")


# ========== Module-level singleton ==========

_service: Optional[NotificationService] = None
_service_lock = Lock()


def get_notification_service() -> NotificationService:
    """
    Get the notification service singleton.

    Creates service on first call (lazy initialization).

    Returns:
        NotificationService instance
    """
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = NotificationService()
    return _service
