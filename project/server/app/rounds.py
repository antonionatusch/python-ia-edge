from __future__ import annotations

import asyncio
import logging
from collections import Counter
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .config import Settings
from .devices import DeviceClient, DeviceError
from .firebase_service import FirebaseNotificationSender
from .notification_devices import NotificationDeviceStore


CLASS_LABELS = {
    "empty": "El comedero parece estar vacío.",
    "food_available": "Hay alimento disponible en el comedero.",
    "unknown": "No se pudo determinar el estado del comedero.",
}
LOGGER = logging.getLogger(__name__)


class RoundCoordinator:
    def __init__(
        self,
        settings: Settings,
        devices: DeviceClient,
        store: NotificationDeviceStore,
        sender: FirebaseNotificationSender,
    ) -> None:
        self.settings = settings
        self.devices = devices
        self.store = store
        self.sender = sender
        self._round_lock = asyncio.Lock()
        self._debug_tasks: set[asyncio.Task[None]] = set()

    async def run_scheduled_round(
        self, scheduled_at: datetime | None = None
    ) -> dict[str, Any]:
        async with self._round_lock:
            return await self._run_scheduled_round(scheduled_at)

    async def _run_scheduled_round(
        self, scheduled_at: datetime | None
    ) -> dict[str, Any]:
        timezone = ZoneInfo(self.settings.round_timezone)
        scheduled_at = scheduled_at or datetime.now(timezone).replace(
            minute=0, second=0, microsecond=0
        )
        round_record = await asyncio.to_thread(
            self.store.create_round,
            scheduled_at=scheduled_at.isoformat(),
            source="automatic",
        )
        if round_record["status"] == "running":
            await asyncio.to_thread(
                self.store.reset_interrupted_round, round_record["id"]
            )
            round_record = await asyncio.to_thread(
                self.store.get_round, round_record["id"]
            )
            if round_record is None:
                raise RuntimeError("Interrupted round could not be recovered")
        if round_record["status"] != "pending":
            return round_record

        try:
            master = await self.devices.master_status()
            if master.get("mode") != "automatic" or not master.get("relay_enabled"):
                await asyncio.to_thread(
                    self.store.set_round_status,
                    round_record["id"],
                    "skipped",
                    error="automatic_round_not_active",
                )
                current = await asyncio.to_thread(
                    self.store.get_round, round_record["id"]
                )
                return current or round_record

            await asyncio.to_thread(
                self.store.set_round_status, round_record["id"], "running"
            )
            results: list[dict[str, Any]] = []
            for sample_index in range(self.settings.round_sample_count):
                try:
                    result = await self.devices.camera_capture_and_classify()
                    results.append(result)
                    await asyncio.to_thread(
                        self.store.add_classification,
                        round_id=round_record["id"],
                        sample_index=sample_index,
                        result=result,
                    )
                except DeviceError as error:
                    await asyncio.to_thread(
                        self.store.add_classification,
                        round_id=round_record["id"],
                        sample_index=sample_index,
                        error=error.reason,
                    )
                if sample_index + 1 < self.settings.round_sample_count:
                    await asyncio.sleep(self.settings.round_sample_interval_seconds)

            result_class, confidence = self._majority_result(results)
            await asyncio.to_thread(
                self.store.set_round_status,
                round_record["id"],
                "completed",
                result=result_class,
                confidence=confidence,
            )
            try:
                await self._send_round_result(
                    round_record["id"], result_class, debug=False
                )
            except Exception:
                # A transient Firebase failure must not invalidate the round result.
                LOGGER.exception("Could not send automatic round notification")
        except Exception as error:
            await asyncio.to_thread(
                self.store.set_round_status,
                round_record["id"],
                "failed",
                error=type(error).__name__,
            )
        current = await asyncio.to_thread(self.store.get_round, round_record["id"])
        return current or round_record

    async def schedule_debug_notification(
        self,
        classification: dict[str, Any],
    ) -> dict[str, Any]:
        now = datetime.now(ZoneInfo(self.settings.round_timezone))
        round_record = await asyncio.to_thread(
            self.store.create_round,
            scheduled_at=now.isoformat(),
            source="debug",
        )
        await asyncio.to_thread(
            self.store.add_classification,
            round_id=round_record["id"],
            sample_index=0,
            result=classification,
        )
        await asyncio.to_thread(
            self.store.set_round_status,
            round_record["id"],
            "completed",
            result=classification["predicted_class"],
            confidence=classification["confidence"],
        )
        task = asyncio.create_task(
            self._send_debug_after_delay(
                round_record["id"], classification["predicted_class"]
            )
        )
        self._debug_tasks.add(task)
        task.add_done_callback(self._debug_tasks.discard)
        return {
            "scheduled": True,
            "round_id": round_record["id"],
            "delay_seconds": self.settings.notification_debug_delay_seconds,
        }

    async def _send_debug_after_delay(self, round_id: int, result: str) -> None:
        await asyncio.sleep(self.settings.notification_debug_delay_seconds)
        try:
            await self._send_round_result(round_id, result, debug=True)
        except Exception:
            LOGGER.exception("Could not send debug round notification")

    async def _send_round_result(self, round_id: int, result: str, *, debug: bool) -> None:
        await asyncio.to_thread(
            self.sender.send,
            title="Prueba de clasificación" if debug else "Ronda completada",
            body=CLASS_LABELS[result],
            data={
                "type": "round_result",
                "round_id": str(round_id),
                "result": result,
                "debug": str(debug).lower(),
            },
            notification_type="debug" if debug else "round_result",
            round_id=round_id,
        )

    def _majority_result(self, results: list[dict[str, Any]]) -> tuple[str, float]:
        valid = [
            result
            for result in results
            if result.get("predicted_class") in CLASS_LABELS
        ]
        if not valid:
            return "unknown", 0.0
        counts = Counter(result["predicted_class"] for result in valid)
        highest = max(counts.values())
        winners = [label for label, count in counts.items() if count == highest]
        winner = winners[0] if len(winners) == 1 else "unknown"
        confidences = [
            float(result.get("confidence", 0))
            for result in valid
            if result["predicted_class"] == winner
        ]
        confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return winner, confidence

    async def close(self) -> None:
        for task in self._debug_tasks:
            task.cancel()
        await asyncio.gather(*self._debug_tasks, return_exceptions=True)
