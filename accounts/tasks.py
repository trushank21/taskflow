from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User # Import User model
import os

@shared_task
def send_password_reset_email(subject, email_template_name, context, to_email):
    # sourcery skip: use-named-expression
    """
    Asynchronous task to send password reset emails.
    Rehydrates the 'user' object from user_id to ensure template compatibility.
    """
    # 1. Rehydrate the User object from the ID passed in context
    user_id = context.get('user')
    if user_id:
        try:
            context['user'] = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            # If the user was deleted between the request and task execution
            return
        
    # 2. Render the email content
    html_message = render_to_string(email_template_name, context)
    plain_message = strip_tags(html_message)

    # 3. Send the mail
    send_mail(
        subject=subject,
        message=plain_message,
        from_email='noreply@taskflow.com',
        recipient_list=[to_email],
        fail_silently=False,
        html_message=html_message,
    )


# @shared_task
# def send_password_reset_email(subject, email_template_name, context, to_email):
#     user_id = context.get('user')
#     if user_id:
#         try:
#             context['user'] = User.objects.get(pk=user_id)
#         except User.DoesNotExist:
#             return
        
#     html_message = render_to_string(email_template_name, context)
    
#     # Send via Brevo API instead of Django's send_mail
#     api_key = os.getenv('BREVO_API_KEY')
    
#     response = requests.post(
#         "https://api.brevo.com/v3/smtp/email",
#         headers={
#             "api-key": api_key,
#             "content-type": "application/json"
#         },
#         json={
#             "sender": {"name": "TaskFlow", "email": "your-verified-email@domain.com"},
#             "to": [{"email": to_email}],
#             "subject": subject,
#             "htmlContent": html_message
#         }
#     )
    
#     if response.status_code != 201:
#         print(f"Failed to send email: {response.text}")