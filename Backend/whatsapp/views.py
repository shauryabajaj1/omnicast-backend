from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .whatsapp import send_whatsapp_message
from django.conf import settings
from django.http import JsonResponse
from twilio.rest import Client
import pandas as pd
from .models import ClientData
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
import matplotlib.pyplot as plt
from django.core.mail import send_mail
from twilio.rest import Client
from django.conf import settings
from .generative_ai import generate_message
from django.contrib.auth.models import User
import csv
import io
from django.http import HttpResponse
from django.contrib.auth import authenticate
from whatsapp.models import UserProfile

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import User
from whatsapp.models import Company, UserProfile
import json
from whatsapp.models import Customer, Company
import google.generativeai as genai
from django.core.mail import EmailMessage, get_connection
from django.contrib.auth import get_user_model
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from django.http import JsonResponse, HttpResponseRedirect
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
whatsapp_messages = []


@csrf_exempt
def register(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("📥 Incoming request data:", data)
            print("🔐 Headers:", dict(request.headers))
            print("🔢 Method:", request.method)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        password = data.get("password")
        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        company_name = data.get("company_name")
        username = f"{first_name} {last_name}"
        print(f"{company_name}hello")
        # Check if username or email already exists
        # if User.objects.filter(username=username).exists():
        #     return JsonResponse({"error": "Username already exists"}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "Email already exists"}, status=400)

        # Create or get company
        company, _ = Company.objects.get_or_create(name=company_name)
        print(company)
        # Create the user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )

        # Create the user profile
        UserProfile.objects.create(user=user, company=company)

        return JsonResponse({
            "message": "User registered successfully",
            "user": {
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "company": company.name
            }
        })

    return JsonResponse({"error": "POST request required"}, status=400)


# @csrf_exempt
# def home(request):
#     if request.method == 'POST':
#         # body_unicode = request.body.decode('utf-8')
#         # data = json.loads(body_unicode)

#         # # Logging request
#         # print("📥 Incoming request data:", data)
#         # print("🔐 Headers:", dict(request.headers))
#         # print("🔢 Method:", request.method)

#         # email = data.get('email')
#         # password = data.get('password')
#         print(f"Login attempt with email: {email}")

#         # Step 1: Try to find user by email
#         try:
#             user = User.objects.get(email=email)
#             print(f"User found: {user.username}")
#         except User.DoesNotExist:
#             print(f"No user found with email: {email}")
#             return JsonResponse({'error': 'Invalid email or password'}, status=401)

#         # Step 2: Authenticate using username and password
#         user = authenticate(request, username=user.username, password=password)

#         if user is not None:
#             print(f"Authentication successful for user: {user.username}")
#             return JsonResponse({
#                 "id": user.id,
#                 "email": user.email,
#                 "username": user.username,
#             })
#         else:
#             print(f"Authentication failed for user: {user.username}")
#             return JsonResponse({'error': 'Invalid email or password'}, status=401)

#     print("Received a non-POST request.")
#     return JsonResponse({'error': 'POST request required'}, status=400)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@csrf_exempt
def home(request):
    if request.method == 'POST':

        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)

        # Logging request
        print("📥 Incoming request data:", data)
        print("🔐 Headers:", dict(request.headers))
        print("🔢 Method:", request.method)

        email = data.get('email')
        password = data.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            profile = UserProfile.objects.get(user=user)
            company = profile.company
            return JsonResponse({
                "id": user.id,
                "email": user.email,
                "First Name": user.first_name,
                "Last Name":user.last_name,
                "Company":company.name,
                "Tenant ID": company.id
            })
        else:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)

    return JsonResponse({'error': 'POST request required'}, status=400)

@csrf_exempt
def get_customers_by_company(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    # Group customers by their group name
    customers = Customer.objects.filter(company=company)
    grouped_customers = {}
    group_colors = {}

    for customer in customers:
        group = customer.group or "Others"
        if group not in grouped_customers:
            grouped_customers[group] = []
            group_colors[group] = customer.color or "#000000"

        grouped_customers[group].append({
            "id": str(customer.id),
            "name": customer.name,
            "email": customer.email,
            "phone":customer.phone_number
        })

    # Prepare group-color map
    group_color_list = [{"name": group, "color": color} for group, color in group_colors.items()]

    return JsonResponse({
        "grouped_customers": grouped_customers,  # File 1 format
        "group_colors": group_color_list         # File 2 format
    })

@csrf_exempt
def send_message(request):
    """API to send WhatsApp messages via POST request."""
    if request.method == "POST":
        data = json.loads(request.body)
        phone_number = data.get("phone_number")
        message = data.get("message")

        if not phone_number or not message:
            return JsonResponse({"error": "Missing phone_number or message"}, status=400)

        response = send_whatsapp_message(phone_number, message)
        return JsonResponse(response)

    return JsonResponse({"error": "Invalid request"}, status=405)

def make_ai_call(request):
    """API to make an AI-powered voice call using Twilio."""
    phone_number = request.GET.get("phone_number", None)
    if not phone_number:
        return JsonResponse({"error": "Phone number is required"}, status=400)

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Generate a Twilio voice call using AI Text-to-Speech
    call = client.calls.create(
        to=phone_number,
        from_=settings.TWILIO_PHONE_NUMBER,
        twiml='<Response><Say>Hello, this is an AI-powered voice call.</Say></Response>'
    )

    return JsonResponse({"message": "Call initiated", "call_sid": call.sid})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def upload_csv(request):
    if request.method == "POST":
        tenant_id = request.GET.get("tenant_id")
        if not tenant_id:
            return JsonResponse({"error": "Missing tenant_id"}, status=400)

        try:
            company = Company.objects.get(id=tenant_id)
        except Company.DoesNotExist:
            return JsonResponse({"error": "Invalid company ID"}, status=400)

        json_file = request.FILES.get("file")
        if not json_file or not json_file.name.endswith(".json"):
            return JsonResponse({"error": "Not a valid JSON file"}, status=400)

        try:
            data = json.load(json_file)
        except Exception as e:
            return JsonResponse({"error": f"Invalid JSON content: {str(e)}"}, status=400)

        if not isinstance(data, list):
            return JsonResponse({"error": "Expected a list of client objects"}, status=400)

        group_name = request.POST.get("name", "Ungrouped")
        group_color = request.POST.get("color", "#808080")

        added = 0
        for row in data:
            try:
                # Save to ClientData
                ClientData.objects.create(
                    tenant=company,
                    name=row["name"],
                    phone_number=row["phone_number"],
                    email=row["email"],
                    revenue=0,
                    interest_level=1,
                )

                # Save to Customer
                Customer.objects.create(
                    company=company,
                    name=row["name"],
                    phone_number=row["phone_number"],
                    email=row["email"],
                    group=group_name,
                    color=group_color
                )

                added += 1
            except Exception as e:
                print(f"⚠️ Error on row {row}: {e}")

        return JsonResponse({"message": f"{added} clients uploaded successfully."})

    return JsonResponse({"error": "POST required"}, status=400)



def generate_graph(request):
    data = ClientData.objects.all()
    names = [client.name for client in data]
    revenues = [client.revenue for client in data]
    interests = [client.interest_level for client in data]

    # Plot
    plt.figure(figsize=(10, 5))
    plt.scatter(revenues, interests, color="blue", alpha=0.6)
    plt.xlabel("Revenue ($)")
    plt.ylabel("Interest Level (1-10)")
    plt.title("Client Revenue vs Interest Level")

    # Save the graph
    graph_path = "media/graph.png"
    plt.savefig(graph_path)

    return FileResponse(open(graph_path, "rb"), content_type="image/png")

def send_email(request, email):
    send_mail(
        "Business Inquiry",
        "Hello, we’d love to discuss business opportunities with you.",
        "yourbusiness@example.com",
        [email],
    )
    return JsonResponse({"message": "Email sent successfully"})

def send_sms(request, phone_number):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body="Hello! We’d love to discuss business opportunities.",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone_number,
    )
    return JsonResponse({"message": "SMS sent successfully"})

def make_call(request, phone_number):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        to=phone_number,
        from_=settings.TWILIO_PHONE_NUMBER,
        twiml='<Response><Say>Hello! We’d love to discuss business opportunities.</Say></Response>'
    )
    return JsonResponse({"message": "Call initiated", "call_sid": call.sid})


def send_whatsapp(request, phone_number):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body="Hello! We’d love to discuss business opportunities.",
        from_="whatsapp:+14155238886",  # Twilio sandbox number
        to=f"whatsapp:{phone_number}",
    )
    return JsonResponse({"message": "WhatsApp message sent successfully"})

@csrf_exempt
def send_bulk_messages(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    data = json.loads(request.body)
    print(data)
    channel = data.get("channel")  # 'sms', 'whatsapp', or 'email'
    message = data.get("message")
    recipients = data.get("recipients", [])  # list of dicts with phone_number and/or email

    if not channel or not recipients or (channel != "call" and not message):
        return JsonResponse({"error": "Missing channel, message, or recipients"}, status=400)

    # Retrieve the stored email credentials from the session
    data = json.loads(request.body)
    user_email = data.get("user_email")

    try:
        user = User.objects.get(email=user_email)
        profile = UserProfile.objects.get(user=user)
        user_email = profile.email_host_user
        user_app_password = profile.email_host_password

        if not user_email or not user_app_password:
            return JsonResponse({"error": "User email or app password not set in profile"}, status=400)

    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "User profile not found"}, status=404)

    results = []

    for r in recipients:
        phone = r.get("phone_number")
        email = r.get("email")
        name = r.get("name", "there")

        try:
            if channel == "whatsapp" and phone:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=message,
                    from_="whatsapp:+14155238886",
                    to=f"whatsapp:{phone}",
                )
                results.append({"status": "sent", "channel": "whatsapp", "to": phone})

            elif channel == "sms" and phone:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone,
                )
                results.append({"status": "sent", "channel": "sms", "to": phone})

            elif channel == "email" and email:
                if user_email and user_app_password:
                    # Create message
                    msg = MIMEMultipart()
                    msg['From'] = user_email
                    msg['To'] = email
                    msg['Subject'] = "Hello"
                    msg.attach(MIMEText(message, 'plain'))

                    # Connect to SMTP server
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()  # Secure the connection
                    server.login(user_email, user_app_password)
                    text = msg.as_string()
                    server.sendmail(user_email, email, text)
                    server.quit()
                    
                    results.append({"status": "sent", "channel": "email", "to": email})
                else:
                    results.append({"status": "error", "channel": "email", "message": "Missing email or app password", "recipient": r})

            elif channel == "call" and phone:
                # AI-powered voice call using Twilio
                call_message = message or "Hello, this is an AI-powered voice call."
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                call = client.calls.create(
                    to=phone,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    twiml=f'<Response><Say>{call_message}</Say></Response>'
                )
                results.append({"status": "call initiated", "channel": "call", "to": phone, "sid": call.sid})

            else:
                results.append({"status": "skipped", "reason": "Missing info", "recipient": r})

        except Exception as e:
            results.append({"status": "error", "error": str(e), "recipient": r})

    return JsonResponse({"results": results})


def generate_message_view(request):
    name = request.GET.get("name", "Customer")
    revenue = request.GET.get("revenue", "10000")

    prompt = f"""
    Write a short and professional message for a client named {name}
    who is potentially worth ${revenue}. Mention how we can help them with our services.
    """

    message = generate_message(prompt)
    return JsonResponse({"message": message})

genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-001')

@csrf_exempt
def gemini_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method is allowed."}, status=405)

    try:
        body = json.loads(request.body)
        user_prompt = body.get("message")
        group_name = body.get("group")
        company_id = body.get("company_id")
        user_name = body.get("name")
        if not user_prompt or not group_name or not company_id:
            return JsonResponse({"error": "Missing one or more required fields: 'prompt', 'group', 'company_id'."}, status=400)

        if group_name == 'all':
            customers = Customer.objects.filter(company_id=company_id).values(
            "name", "email", "phone_number"
        )
        elif group_name == 'none':
            customers = Customer.objects.filter(company_id=company_id, group=group_name).values(
            "name", "email", "phone_number"
        )
        else:
            customers = Customer.objects.filter(company_id=company_id, group=group_name).values(
                "name", "email", "phone_number"
            )
        customer_list = list(customers)

        company = Company.objects.get(id=company_id)
        company_name = company.name
        print(user_name)
        print(company_name)
        # Prepare contextual prompt
        context_json = json.dumps(customer_list, indent=2)
        print(context_json)
        prompt = (
            f"You are an assistant helping {user_name} from {company_name} craft messages to groups of clients.\n"
            "Here is a list of clients in JSON format:\n"
            f"{context_json}\n\n"
            "Please respond in plain text only (no markdown). "
            "Using this data, " + user_prompt
        )

        response = model.generate_content(prompt)
        return JsonResponse({"reply": response.text.strip()})

    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return JsonResponse({"error": f"Something went wrong: {str(e)}"}, status=500)
    
# goxe rvmt dndi qsme
# @csrf_exempt
# def get_messages(request):
#     # messages = [
#     #     {
#     #         "group": "Sales",
#     #         "sender": "Nishchay Yadav",
#     #         "message": "Hey, got your email. All good!",
#     #         "time": "2 mins ago",
#     #         "channel": "Email",
#     #     },
#     #     {
#     #         "group": "Sales",
#     #         "sender": "Aditi Sharma",
#     #         "message": "Confirmed the meeting for 3 PM.",
#     #         "time": "10 mins ago",
#     #         "channel": "WhatsApp",
#     #     },
#     #     {
#     #         "group": "Market",
#     #         "sender": "Mom",
#     #         "message": "Dinner at 8 tonight.",
#     #         "time": "1 hour ago",
#     #         "channel": "SMS",
#     #     },
#     # ] * 1  # Repeat 4 times for total 12 messages as in your example
#     messages = []

#     messages.extend(whatsapp_messages)

#     email_account = 'shaurya173@gmail.com'
#     email_password = 'goxervmtdndiqsme'

#     if email_account and email_password:
#         try:
#             imap_server = "imap.gmail.com"
#             mail = imaplib.IMAP4_SSL(imap_server)
#             mail.login(email_account, email_password)
#             mail.select("inbox")

#             status, data = mail.search(None, "ALL")
#             if status == "OK":
#                 email_ids = data[0].split()
#                 latest_ids = email_ids[-5:]  # Get last 5 messages

#                 for email_id in reversed(latest_ids):
#                     status, msg_data = mail.fetch(email_id, "(RFC822)")
#                     if status != "OK":
#                         continue

#                     for response_part in msg_data:
#                         if isinstance(response_part, tuple):
#                             msg = email.message_from_bytes(response_part[1])

#                             subject, encoding = decode_header(msg.get("Subject"))[0]
#                             if isinstance(subject, bytes):
#                                 subject = subject.decode(encoding or "utf-8", errors="ignore")

#                             sender_raw = msg.get("From")
#                             sender_name, sender_email = parseaddr(sender_raw)
#                             timestamp = msg.get("Date")

#                             messages.append({
#                                 "group": "Sales",
#                                 "sender_name": sender_name,
#                                 "sender_email": sender_email,
#                                 "message": subject,
#                                 "time": timestamp,
#                                 "channel": "Email",
#                             })

#             mail.logout()
#         except Exception as e:
#             # Optionally, log error or include in response
#             print(f"Email fetch error: {e}")

#     print(messages)
#     return JsonResponse(messages, safe=False)

@csrf_exempt
def get_messages(request):
    messages = []

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        user_email_input = data.get("user_email")
        if not user_email_input:
            return JsonResponse({"error": "Missing user_email parameter"}, status=400)

        # Fetch user and profile from DB
        user = User.objects.get(email=user_email_input)
        profile = UserProfile.objects.get(user=user)

        user_email = profile.email_host_user
        user_app_password = profile.email_host_password
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        return JsonResponse({"error": "UserProfile not found for this user"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)

    if user_email and user_app_password:
        try:
            imap_server = "imap.gmail.com"
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(user_email, user_app_password)
            mail.select("inbox")

            status, data = mail.search(None, "ALL")
            if status == "OK":
                email_ids = data[0].split()
                latest_ids = email_ids[-5:]

                for email_id in reversed(latest_ids):
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        continue

                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])

                            subject, encoding = decode_header(msg.get("Subject"))[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding or "utf-8", errors="ignore")

                            sender_raw = msg.get("From")
                            sender_name, sender_email = parseaddr(sender_raw)
                            timestamp = msg.get("Date")

                            messages.append({
                                "group": "Sales",
                                "sender_name": sender_name,
                                "sender_email": sender_email,
                                "message": subject,
                                "time": timestamp,
                                "channel": "Email",
                            })

            mail.logout()
        except Exception as e:
            print(f"Email fetch error: {e}")

    print(messages)
    return JsonResponse(messages, safe=False)





@csrf_exempt
def google_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        if not email:
            return JsonResponse({"error": "Email is required"}, status=400)

        user, created = User.objects.get_or_create(email=email, defaults={
            "username": email,  # or use a UUID
            "first_name": first_name,
            "last_name": last_name,
            "password": User.objects.make_random_password(),  # random, unused
        })

        # Optionally: create a profile or company if new user
        if created:
            company = Company.objects.create(name=f"{first_name}'s Company")
            UserProfile.objects.create(user=user, company=company)

        return JsonResponse({
            "message": "User synced",
            "user_id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })

    return JsonResponse({"error": "POST required"}, status=400)

# Gmail read-only scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def gmail_auth(request):
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    flow.redirect_uri = 'http://localhost:8000/oauth2callback/'
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    request.session['flow'] = flow.credentials_to_dict(flow)
    return HttpResponseRedirect(auth_url)

def oauth2callback(request):
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    flow.fetch_token(code=request.GET.get('code'))
    creds = flow.credentials

    # Store creds in session or DB
    request.session['token'] = creds.to_json()
    return JsonResponse({"message": "Authenticated!"})

def get_replies(request):
    from google.oauth2.credentials import Credentials
    creds = Credentials.from_authorized_user_info(json.loads(request.session['token']), SCOPES)
    service = build('gmail', 'v1', credentials=creds)

    # Example: search for replies with subject "Re: Business Inquiry"
    results = service.users().messages().list(
        userId='me', q='subject:"Re: Business Inquiry" newer_than:7d'
    ).execute()

    messages = results.get('messages', [])
    replies = []

    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = msg_detail.get('snippet')
        headers = {h['name']: h['value'] for h in msg_detail['payload']['headers']}
        replies.append({
            "from": headers.get("From"),
            "subject": headers.get("Subject"),
            "snippet": snippet,
        })

    return JsonResponse({"replies": replies})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

# @csrf_exempt
# def store_email_credentials(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Invalid request method"}, status=405)

#     try:
#         data = json.loads(request.body)
#         user = data.get("user_email")
#         email = data.get("email")
#         app_password = data.get("app_password")
#         if not email or not app_password:
#             return JsonResponse({"error": "Missing email or app password"}, status=400)

#         # Store in session (or database or secure vault if needed)
#         request.session['email'] = email
#         request.session['app_password'] = app_password
#         print(f"Stored email: {email} and app password: {app_password}")  # Debugging line
#         return JsonResponse({"message": "Credentials stored successfully"})
#     except json.JSONDecodeError:
#         return JsonResponse({"error": "Invalid JSON"}, status=400)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.contrib.auth.models import User
from .models import UserProfile

@csrf_exempt
def store_email_credentials(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        user_email = data.get("user_email")
        email = data.get("email")
        app_password = data.get("app_password", "")

        if not user_email or not email:
            return JsonResponse({"error": "Missing user email or email account"}, status=400)

        try:
            user = User.objects.get(email=user_email)
            profile, _ = UserProfile.objects.get_or_create(user=user)

            profile.email_host_user = email
            profile.email_host_password = app_password
            profile.save()
            print(f"Stored email: {email} and app password: {app_password}")  # Debugging line
            return JsonResponse({"message": "Credentials stored successfully"})
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

@csrf_exempt
def twilio_incoming_message(request):
    if request.method == 'POST':
        from_number = request.POST.get('From')
        to_number = request.POST.get('To')
        body = request.POST.get('Body')

        # Log or save the response to DB
        print(f"Message from {from_number}: {body}")

        # You can reply if you want
        return HttpResponse("<Response><Message>Thanks for your message!</Message></Response>", content_type='text/xml')

    return HttpResponse("Invalid request", status=400)

@csrf_exempt
def check_inbox(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
        email_user = data.get("email")
        app_password = data.get("app_password")

        if not email_user or not app_password:
            return JsonResponse({"error": "Missing credentials"}, status=400)

        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, app_password)
        mail.select("inbox")

        # Search for unread messages
        status, messages = mail.search(None, '(UNSEEN)')
        email_ids = messages[0].split()

        output = []

        for e_id in email_ids[-5:]:  # Get last 5 unseen
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            from_ = msg.get("From")
            snippet = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        snippet = part.get_payload(decode=True).decode()
                        break
            else:
                snippet = msg.get_payload(decode=True).decode()

            output.append({
                "from": from_,
                "subject": subject,
                "snippet": snippet[:100]  # Limit snippet length
            })

        mail.logout()
        return JsonResponse({"messages": output})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def check_email_inbox(request):
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    email_address = request.session.get('email')
    app_password = request.session.get('app_password')

    if not email_address or not app_password:
        return JsonResponse({"error": "Missing credentials in session"}, status=400)

    try:
        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, app_password)
        mail.select("inbox")

        # Search for all messages
        result, data = mail.search(None, "ALL")
        mail_ids = data[0].split()[-5:]  # Last 5 messages

        emails = []

        for mail_id in reversed(mail_ids):
            result, msg_data = mail.fetch(mail_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            from_ = msg.get("From")
            snippet = ""

            # Get plain text part
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        snippet = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                snippet = msg.get_payload(decode=True).decode(errors="ignore")

            emails.append({
                "from": from_,
                "subject": subject,
                "snippet": snippet[:200]
            })

        return JsonResponse({"emails": emails})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from django.utils import timezone
from django.views.decorators.http import require_POST
from django.utils.timezone import now

@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    from_number = request.POST.get('From')
    message_body = request.POST.get('Body')
    timestamp = request.POST.get('Timestamp') or timezone.now().strftime("%Y-%m-%d %H:%M")

    # Add to the global list
    whatsapp_messages.append({
        "group": "Sales",
        "sender_number": from_number[9:],
        "message": message_body,
        "time": timestamp,
        "channel": "WhatsApp",
    })
    print(whatsapp_messages)

    print(f"WhatsApp message from {from_number}: {message_body}")
    return JsonResponse({"status": "received"})

from django.contrib.auth.decorators import login_required


@csrf_exempt
def check_email_credentials(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        user_email = data.get("user_email")
        if not user_email:
            return JsonResponse({"error": "Missing user_email parameter"}, status=400)

        # Get User and corresponding UserProfile
        user = User.objects.get(email=user_email)
        user_profile = UserProfile.objects.get(user=user)
        email = user_profile.email_host_user
        password = user_profile.email_host_password

        return JsonResponse({
            "credentials_present": bool(email and password),
            "email": email or "",
            "app_password": password or ""
        })
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        return JsonResponse({
            "credentials_present": False,
            "email": "",
            "app_password": ""
        })
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
