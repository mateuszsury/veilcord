"""
CPU and GPU resource monitoring for effects processing.

Provides real-time monitoring of CPU/GPU usage to display performance
indicators and warn users about resource consumption.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """
    Monitor CPU and GPU resource usage.

    Provides periodic monitoring of system resources to:
    - Display CPU/GPU usage indicator in UI
    - Warn users if processing is too heavy
    - Help users decide quality preset

    Usage:
        monitor = ResourceMonitor()
        cpu_usage = monitor.get_cpu_usage()  # 0-100
        gpu_usage = monitor.get_gpu_usage()  # 0-100 or None

        # Async monitoring
        await monitor.start_monitoring(interval=1.0)
        # ... later
        monitor.stop_monitoring()
    """

    def __init__(self):
        """Initialize resource monitor (monitoring disabled by default)."""
        self._monitoring_enabled = False
        self._monitoring_task: Optional[asyncio.Task] = None

    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage percentage.

        Returns:
            CPU usage as percentage (0-100)
        """
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            logger.warning("psutil not installed - CPU monitoring unavailable")
            return 0.0
        except Exception as e:
            logger.error("Failed to get CPU usage: %s", e)
            return 0.0

    def get_gpu_usage(self) -> Optional[float]:
        """
        Get current GPU usage percentage (NVIDIA only).

        Returns:
            GPU usage as percentage (0-100), or None if:
            - GPUtil not installed
            - No NVIDIA GPU detected
            - GPU monitoring failed
        """
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                # Return usage of first GPU (most systems have one)
                return gpus[0].load * 100
            else:
                return None
        except ImportError:
            # GPUtil not installed (it's optional)
            return None
        except Exception as e:
            logger.debug("GPU monitoring unavailable: %s", e)
            return None

    def get_memory_usage(self) -> float:
        """
        Get current system memory usage percentage.

        Returns:
            Memory usage as percentage (0-100)
        """
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            logger.warning("psutil not installed - memory monitoring unavailable")
            return 0.0
        except Exception as e:
            logger.error("Failed to get memory usage: %s", e)
            return 0.0

    async def start_monitoring(
        self,
        interval: float = 1.0,
        callback: Optional[callable] = None
    ) -> None:
        """
        Start periodic resource monitoring.

        Monitors CPU/GPU usage at specified interval and optionally calls
        a callback with the results.

        Args:
            interval: Monitoring interval in seconds (default: 1.0)
            callback: Optional callback(cpu, gpu, memory) called each interval
        """
        if self._monitoring_enabled:
            logger.warning("Monitoring already started")
            return

        self._monitoring_enabled = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval, callback)
        )
        logger.info("Resource monitoring started (interval: %.1fs)", interval)

    async def _monitoring_loop(
        self,
        interval: float,
        callback: Optional[callable]
    ) -> None:
        """Internal monitoring loop."""
        while self._monitoring_enabled:
            try:
                cpu = self.get_cpu_usage()
                gpu = self.get_gpu_usage()
                memory = self.get_memory_usage()

                if callback:
                    try:
                        callback(cpu, gpu, memory)
                    except Exception as e:
                        logger.error("Monitoring callback failed: %s", e)

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Monitoring loop error: %s", e)
                await asyncio.sleep(interval)

    def stop_monitoring(self) -> None:
        """Stop periodic resource monitoring."""
        if not self._monitoring_enabled:
            return

        self._monitoring_enabled = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None
        logger.info("Resource monitoring stopped")

    @property
    def is_monitoring(self) -> bool:
        """True if periodic monitoring is active."""
        return self._monitoring_enabled
