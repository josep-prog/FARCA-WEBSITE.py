mport smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

# Example function to send email notifications
def send_email_notification(recipient, subject, body):
    sender_email = "youremail@example.com"
    sender_password = "yourpassword"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())

# Example function to send SMS notifications
def send_sms_notification(phone_number, message):
    account_sid = 'your_twilio_account_sid'
    auth_token = 'your_twilio_auth_token'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=message,
        from_='+1234567890',
        to=phone_number
    )

# Example function to calculate delivery cost
def calculate_delivery_cost(distance):
    base_cost = 1500
    cost_per_km = 200
    return base_cost + (cost_per_km * distance)
