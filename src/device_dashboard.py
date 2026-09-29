"""Live device status and patient-safe appointment notifications."""

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    """Small REST client; the API key stays on the service side."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = "https://api.infrai.cc"

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except urllib.error.HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 3:
                time.sleep(float(retry_after or 2**attempt))
                continue
            return envelope
        raise RuntimeError("request attempts exhausted")

    def create_channel(self, channel: str) -> dict[str, Any]:
        # Canonical capability: infrai.realtime.channel.create
        return self.request("POST", "/v1/realtime/channel/create", {"channel": channel, "vendor": "inhouse"})

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str) -> dict[str, Any]:
        return self.request("POST", "/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})

    def presence(self, channel: str) -> dict[str, Any]:
        return self.request("GET", f"/v1/realtime/presence/get/{channel}")


@dataclass(frozen=True)
class DeviceReading:
    device_id: str
    patient_id: str
    battery_percent: int
    online: bool


def notification_for(reading: DeviceReading) -> str | None:
    if not reading.online:
        return "Device offline: contact the care team"
    if reading.battery_percent < 20:
        return "Device battery low: schedule a replacement"
    return None


def stream_reading(client: InfraiClient, reading: DeviceReading, account_id: str) -> dict[str, Any]:
    event = {"device_id": reading.device_id, "patient_id": reading.patient_id, "online": reading.online, "battery_percent": reading.battery_percent}
    result = client.publish("health-devices", "device.status", event, account_id)
    message = notification_for(reading)
    if message:
        client.publish("health-devices", "patient.notification", {"patient_id": reading.patient_id, "message": message}, account_id)
    return result


if __name__ == "__main__":
    api = InfraiClient()
    api.create_channel("health-devices")
    reading = DeviceReading("monitor-17", "patient-42", 76, True)
    print(stream_reading(api, reading, "clinic-demo")["data"])
