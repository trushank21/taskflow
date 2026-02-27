from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User # Import User model

@shared_task
def send_password_reset_email(subject, email_template_name, context, to_email):
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