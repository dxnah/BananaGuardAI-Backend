"""
sms.py - sends text messages (SMS) through Semaphore, a Philippine SMS service.

Set these in Railway > your backend > Variables:
    SEMAPHORE_API_KEY       your Semaphore API key
    SEMAPHORE_SENDER_NAME   optional, only if Semaphore approved a custom sender name

For testing without an SMS account, set   SMS_DEV_MODE=true
The text is then printed in the Railway logs instead of being sent.
Turn it OFF before real use: anyone who can read the logs could see the codes.
"""
import os
import requests

SEMAPHORE_URL = "https://api.semaphore.co/api/v4/messages"


def dev_mode() -> bool:
    return os.getenv("SMS_DEV_MODE", "").strip().lower() == "true"


def sms_configured() -> bool:
    return dev_mode() or bool(os.getenv("SEMAPHORE_API_KEY"))


def send_sms(number: str, message: str) -> bool:
    """Send one text to a mobile number like 09171234567.
    Returns True if the message was handed to the SMS service."""
    if dev_mode():
        print(f"[SMS_DEV_MODE] to {number}: {message}")
        return True

    api_key = os.getenv("SEMAPHORE_API_KEY")
    if not api_key:
        return False

    data = {"apikey": api_key, "number": number, "message": message}
    sender = os.getenv("SEMAPHORE_SENDER_NAME")
    if sender:
        data["sendername"] = sender

    try:
        response = requests.post(SEMAPHORE_URL, data=data, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        print("SMS sending failed:", exc)
        return False