from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class WhatsAppMessage(models.Model):
    phone_number = models.CharField(max_length=15)
    message_body = models.TextField()
    status = models.CharField(max_length=50, default='pending')  # sent, delivered, failed
    timestamp = models.DateTimeField(auto_now_add=True)


class Company(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class ClientData(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    revenue = models.FloatField()
    interest_level = models.IntegerField()
    tenant = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)  # ✅ updated

    def __str__(self):
        return f"{self.name} ({self.email})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    # Email sending credentials per user
    email_host_user = models.EmailField(null=True, blank=True)
    email_host_password = models.CharField(max_length=128, null=True, blank=True)
    email_host = models.CharField(max_length=100, default="smtp.gmail.com")
    email_port = models.IntegerField(default=587)
    use_tls = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"

class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()

    # New fields
    group = models.CharField(max_length=50, default='General')  # e.g., 'Friends', 'Work'
    color = models.CharField(max_length=7, default='#000000')   # e.g., '#F43F5E'

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.group}"
    
class IncomingMessage(models.Model):
    from_number = models.CharField(max_length=100)
    to_number = models.CharField(max_length=100)
    body = models.TextField()
    channel = models.CharField(max_length=20)  # 'sms', 'whatsapp', 'email'
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.channel.upper()} | {self.from_number} -> {self.to_number}"