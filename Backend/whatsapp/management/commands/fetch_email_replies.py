from django.core.management.base import BaseCommand
from whatsapp.models import IncomingMessage, UserProfile
from imapclient import IMAPClient
import email
from email.header import decode_header
import datetime

class Command(BaseCommand):
    help = "Fetch email replies using IMAP"

    def handle(self, *args, **kwargs):
        for profile in UserProfile.objects.exclude(email_host_user__isnull=True):
            try:
                with IMAPClient(profile.email_host, ssl=True) as client:
                    client.login(profile.email_host_user, profile.email_host_password)
                    client.select_folder("INBOX", readonly=True)

                    messages = client.search(['UNSEEN'])
                    for uid, message_data in client.fetch(messages, ['RFC822']).items():
                        raw_email = message_data[b'RFC822']
                        msg = email.message_from_bytes(raw_email)

                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8")

                        from_email = msg.get("From")
                        to_email = msg.get("To")

                        # Get the email body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))

                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode(errors="ignore")

                        # Save to DB
                        IncomingMessage.objects.create(
                            from_number=from_email,
                            to_number=to_email,
                            body=body.strip(),
                            channel="email"
                        )

                        print(f"✔️ Fetched email from {from_email}")

            except Exception as e:
                print(f"❌ Error for {profile.user.username}: {e}")