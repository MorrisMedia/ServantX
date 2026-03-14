from .email_service import send_email_html
from config import settings
from .logger_service import error_log
from typing import Optional


async def send_registration_email(
    user_email: str,
    user_name: str,
    verification_link: Optional[str] = None
) -> bool:
    """
    Send registration welcome email to new user

    Args:
        user_email: User email address
        user_name: User's name
        verification_link: Optional email verification link

    Returns:
        bool: True if email sent successfully
    """
    try:
        subject = f"Welcome to {settings.APP_NAME}!"
        
        template_context = {
            "subject": subject,
            "user_name": user_name,
            "user_email": user_email,
            "verification_link": verification_link
        }

        return await send_email_html(
            to_email=user_email,
            subject=subject,
            template_name="registration.html",
            template_context=template_context
        )
    except Exception as e:
        error_log(
            action="send_registration_email",
            error=str(e),
            user_email=user_email,
            user_name=user_name
        )
        return False


async def send_password_reset_email(
    to_email: str,
    reset_code: str,
    reset_url: str,
    user_name: Optional[str] = None
) -> bool:
    """
    Send password reset email with code

    Args:
        to_email: User email address
        reset_code: 6-digit reset code
        reset_url: Password reset URL
        user_name: User's name (optional)

    Returns:
        bool: True if email sent successfully
    """
    try:
        subject = f"Password Reset - {settings.APP_NAME}"
        
        template_context = {
            "subject": subject,
            "reset_code": reset_code,
            "reset_url": reset_url,
            "user_name": user_name or "User"
        }

        return await send_email_html(
            to_email=to_email,
            subject=subject,
            template_name="password_reset.html",
            template_context=template_context
        )
    except Exception as e:
        error_log(
            action="send_password_reset_email",
            error=str(e),
            user_email=to_email
        )
        return False


async def send_welcome_email(
    to_email: str,
    user_name: Optional[str] = None,
    login_url: Optional[str] = None
) -> bool:
    """
    Send welcome email to new user

    Args:
        to_email: User email address
        user_name: User's name (optional)
        login_url: Login URL (optional)

    Returns:
        bool: True if email sent successfully
    """
    try:
        subject = f"Welcome to {settings.APP_NAME}!"
        
        if not login_url:
            login_url = f"{settings.FRONTEND_URL}/login"
        
        template_context = {
            "subject": subject,
            "login_url": login_url
        }

        return await send_email_html(
            to_email=to_email,
            subject=subject,
            template_name="welcome.html",
            template_context=template_context
        )
    except Exception as e:
        error_log(
            action="send_welcome_email",
            error=str(e),
            user_email=to_email
        )
        return False

