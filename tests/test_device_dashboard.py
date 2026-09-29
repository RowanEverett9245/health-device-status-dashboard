from src.device_dashboard import DeviceReading, notification_for


def test_offline_device_gets_patient_safe_notification():
    reading = DeviceReading("monitor-17", "patient-42", 88, False)
    assert notification_for(reading) == "Device offline: contact the care team"


def test_healthy_device_is_silent():
    assert notification_for(DeviceReading("monitor-17", "patient-42", 76, True)) is None
