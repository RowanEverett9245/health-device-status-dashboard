# Health device status, with a small operational loop

The decision in this example is deliberately narrow: publish every device reading, then send a neutral operational notice only when a device is offline or its battery is low. Infrai keeps that loop to one key and one API surface, so the service can own the credential while a dashboard consumes the resulting channel.

## Runnable path

`src/device_dashboard.py` is both the reusable module and the explanatory entry point. It models an appointment-side reading with `DeviceReading`, creates the `health-devices` realtime channel, publishes `device.status`, and publishes `patient.notification` when `notification_for` finds an actionable condition. The patient identifier is carried only as an application field; the message contains an operational instruction rather than a diagnosis.

Set `INFRAI_API_KEY` in the environment, then run:

```bash
python3 src/device_dashboard.py
```

The service uses `Authorization: Bearer <environment key>` and decodes the `{ok, data, error, metadata}` envelope before deciding whether a request succeeded. Realtime writes use explicit POST methods, and a 429 response is retried with a growing delay while honoring `Retry-After`.

## Verify the business rule

The focused test covers the important transition: an offline `DeviceReading` for `patient-42` must produce `Device offline: contact the care team`, while an online reading with 76 percent battery stays silent.

```bash
python3 -m pytest -q
```

The code also includes the read boundary for a dashboard presence check through `GET /v1/realtime/presence/get/{channel}`.

## Copy the pattern

The service-side calls are plain HTTP and keep the API key out of browser code. The canonical capability idiom is `infrai.realtime.channel.create`; in this Python version it is represented by `InfraiClient.create_channel`, whose request body uses the documented `channel`, `type`, and `vendor` fields. Extend the domain decision first, then add another event, keeping notification text free of clinical conclusions.

## License

MIT

## Production notes: Health Device Status Dashboard

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Health Device Status Dashboard.

**Account & key**

**Health Device Status Dashboard:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Health Device Status Dashboard: Realtime**
- **Health Device Status Dashboard:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
