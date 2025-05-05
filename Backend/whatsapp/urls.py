from django.urls import path
from .views import send_message
from django.urls import path
from .views import make_ai_call
from django.urls import path
from .views import upload_csv, generate_graph, send_email, send_whatsapp, send_sms, make_call, generate_message_view, register, gemini_chat, get_messages
from django.contrib import admin
from django.urls import path, include
from .views import home
from .views import get_customers_by_company, whatsapp_webhook
from .views import send_bulk_messages, gmail_auth, oauth2callback, get_replies, store_email_credentials, twilio_incoming_message, check_inbox, check_email_inbox
from django.http import JsonResponse
from .views import check_email_credentials
urlpatterns = [
    path('register/', register, name='register'),
    path("send-whatsapp/", send_message, name="send-whatsapp"),
    path('call/', make_ai_call, name='make_ai_call'),
    path('upload/', upload_csv, name='upload_csv'),
    path('graph/', generate_graph, name='generate_graph'),
    path('email/<str:email>/', send_email, name='send_email'),
    path('whatsapp/<str:phone_number>/', send_whatsapp, name='send_whatsapp'),
    path('sms/<str:phone_number>/', send_sms, name='send_sms'),
    path('call/<str:phone_number>/', make_call, name='make_call'),
    path("generate-message/", gemini_chat, name="generate_message"),
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path('customers/<int:company_id>/', get_customers_by_company, name='get_customers_by_company'),
    path("send_bulk_messages/", send_bulk_messages, name="send_bulk_messages"),
    path("ping/", lambda request: JsonResponse({"ping": "pong"})),
    path("get-messages/", get_messages, name="get_messages"),
    path("gmail_auth/", gmail_auth, name="gmail_auth"),
    path("oauth2callback/", oauth2callback, name="oauth2callback"),
    path("get-replies/", get_replies, name="get_replies"),
    path("store-email-creds/", store_email_credentials, name="store_email_credentials"),
    path('twilio/incoming/', twilio_incoming_message, name='twilio_incoming'),
    path("check-email-inbox/", check_inbox, name="check_email_inbox"),
    path("check_email_inbox/", check_email_inbox, name="check_email_inbox"),
    path("twilio/whatsapp-webhook/", whatsapp_webhook, name="whatsapp_webhook"),
    path('check-email-creds/', check_email_credentials)
]


