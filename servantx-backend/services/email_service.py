import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from schemas import ContactRequest


def format_email_body(data: ContactRequest) -> str:
    """Format the contact request data into an email body"""
    body = f"""
New Contact Form Submission

Organization Information:
- Organization Name: {data.orgName}
- State: {data.state}
- Hospital Type: {', '.join(data.hospitalType) if data.hospitalType else 'Not specified'}
- Revenue: {data.revenue}

Contact Information:
- Name: {data.contactName}
- Role: {data.role}
- Email: {data.email}
- Phone: {data.phone if data.phone else 'Not provided'}

Interest & Requirements:
- Interest Areas: {', '.join(data.interestAreas)}
- Payers: {data.payers if data.payers else 'Not specified'}
- Timeframe: {data.timeframe}
- Approval Status: {data.approval}
- Next Step: {data.nextStep}

Additional Information:
{data.additionalInfo if data.additionalInfo else 'None provided'}
"""
    return body.strip()


def send_contact_email(data: ContactRequest) -> dict:
    """
    Send contact form submission via SendGrid
    
    Returns:
        dict: Response with status and message
    """
    # Get SendGrid configuration from environment
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")
    from_name = os.getenv("SENDGRID_FROM_NAME")
    to_emails_str = os.getenv("SENDGRID_TO_EMAIL")

    if not api_key or not from_email:
        raise ValueError("Email service configuration is missing: SENDGRID_API_KEY and SENDGRID_FROM_EMAIL are required")

    if not to_emails_str:
        raise ValueError("SENDGRID_TO_EMAIL is required")

    # Parse comma-separated email addresses
    to_emails = [email.strip() for email in to_emails_str.split(",") if email.strip()]

    if not to_emails:
        raise ValueError("SENDGRID_TO_EMAIL must contain at least one valid email address")

    # Create email
    message = Mail(
        from_email=(from_email, from_name or "ServantX"),
        to_emails=to_emails,
        subject=f"New Contact Form Submission from {data.orgName}",
        plain_text_content=format_email_body(data)
    )

    # Send email
    sg = SendGridAPIClient(api_key)
    response = sg.send(message)

    # Check if email was sent successfully (2xx status codes)
    if 200 <= response.status_code < 300:
        return {
            "status": "success",
            "message": "Contact form submitted successfully"
        }
    else:
        raise Exception(f"Failed to send email. Status code: {response.status_code}")

