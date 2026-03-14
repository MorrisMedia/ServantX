from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import settings
from .logger_service import info_log, error_log
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Jinja2 environment
template_dir = Path(os.getenv("EMAIL_TEMPLATES_DIR", str(Path(__file__).parent.parent / "email_templates")))
env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(['html', 'xml'])
)


async def send_email_html(
    to_email: str,
    subject: str,
    html_content: Optional[str] = None,
    template_name: Optional[str] = None,
    template_context: Optional[dict] = None
) -> bool:
    """
    Send email using SendGrid

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content of the email (if template_name is not provided)
        template_name: Name of the template file to render (e.g., "registration.html")
        template_context: Dictionary of variables to pass to the template

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        if not settings.SENDGRID_API_KEY:
            error_log(
                action="send_email",
                function_name="send_email_html",
                file_name="email_service.py",
                error="SENDGRID_API_KEY not configured",
                to_email=to_email
            )
            return False

        if not settings.FROM_EMAIL:
            error_log(
                action="send_email",
                function_name="send_email_html",
                file_name="email_service.py",
                error="FROM_EMAIL not configured",
                to_email=to_email
            )
            return False

        if template_name:
            if template_context is None:
                template_context = {}
            html_content = render_email_template(template_name, **template_context)
        elif html_content is None:
            error_log(
                action="send_email",
                function_name="send_email_html",
                file_name="email_service.py",
                error="Either html_content or template_name must be provided",
                to_email=to_email
            )
            return False

        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        # Send email
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in [200, 201, 202]:
            info_log(
                action="send_email",
                status="success",
                to_email=to_email,
                subject=subject,
                status_code=response.status_code
            )
            return True
        else:
            error_log(
                action="send_email",
                function_name="send_email_html",
                file_name="email_service.py",
                error=f"Email send failed with status code {response.status_code}",
                to_email=to_email,
                subject=subject,
                status_code=response.status_code,
                response_body=response.body
            )
            return False

    except Exception as e:
        error_log(
            action="send_email",
            function_name="send_email_html",
            file_name="email_service.py",
            error=str(e),
            to_email=to_email,
            subject=subject
        )
        return False


def render_email_template(template_name: str, **kwargs) -> str:
    """
    Render an email template with the provided context

    Args:
        template_name: Name of the template file (e.g., "registration.html")
        **kwargs: Template variables

    Returns:
        str: Rendered HTML content

    Raises:
        Exception: If template rendering fails
    """
    try:
        template = env.get_template(template_name)
        # Merge app settings with provided kwargs
        context = {
            "app_name": settings.APP_NAME,
            **kwargs
        }
        return template.render(**context)
    except Exception as e:
        error_log(
            action="render_email_template",
            function_name="render_email_template",
            file_name="email_service.py",
            error=str(e),
            template_name=template_name
        )
        raise


