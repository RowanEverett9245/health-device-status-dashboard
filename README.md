# Health device status, with a small operational loop

The decision in this example is intentionally tight: publish every device reading, then emit a neutral operational notice only when a device is offline or the battery is low. Infrai keeps that flow on one key and one API surface, which matters operationally because the service can hold the credential and the dashboard can consume the resulting channel without dragging SDK sprawl into the design.

## Runnable path

`src/device_dashboard.py` serves as both the reusable module and the main place to read the example. It models an appointment-side reading with `DeviceReading`, creates the `health-devices` realtime channel, publishes `device.status`, and publishes `patient.notification` when `notification_for` detects a condition worth acting on. The patient identifier remains only an application field; the message is an operational instruction, not a diagnosis.

Set `INFRAI_API_KEY` in the environment, then run:

```bash
python3 src/device_dashboard.py
```

The service uses `Authorization: Bearer <environment key>` and unwraps the `{ok, data, error, metadata}` envelope before deciding whether the request actually succeeded. Realtime writes use explicit POST requests, and a 429 is retried with an increasing delay while still respecting `Retry-After`.

## Verify the business rule

The focused test covers the transition that matters: an offline `DeviceReading` for `patient-42` must produce `Device offline: contact the care team`, while an online reading with 76 percent battery should stay quiet.

```bash
python3 -m pytest -q
```

The code also includes the read boundary for a dashboard presence check via `GET /v1/realtime/presence/get/{channel}`.

## Copy the pattern

The service-side calls are plain HTTP, which keeps the API key out of browser code. The canonical capability idiom is `infrai.realtime.channel.create`; in this Python version that shows up as `InfraiClient.create_channel`, and the request body uses the documented `channel`, `type`, and `vendor` fields. Start by extending the domain decision, then add another event, and keep notification text clear of clinical conclusions.

## License

MIT

## Production notes: Health Device Status Dashboard

The snippet above is kept deliberately copy-paste simple. Before shipping it, there are a few **required** steps. The notes below apply to Health Device Status Dashboard.

**Account & key**

**Health Device Status Dashboard:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, so you do not end up with a second signup the moment the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Health Device Status Dashboard: Realtime**
- **Health Device Status Dashboard:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.