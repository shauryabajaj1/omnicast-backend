import requests
from django.conf import settings

def send_whatsapp_message(to, message):
    """Send a WhatsApp message using WhatsApp Cloud API."""
    url = f"{settings.WHATSAPP_API_URL}{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,  # Example: "+919876543210"
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()
