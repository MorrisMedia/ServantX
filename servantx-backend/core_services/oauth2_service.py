from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import httpx
from config import settings
from .logger_service import error_log, info_log
from models import User
from .auth_service import create_oauth_token, _get_user_by_email, create_user

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
FACEBOOK_USER_INFO_URL = "https://graph.facebook.com/me"


async def login_with_google(
    db: AsyncSession,
    authorization_code: str,
    redirect_uri: str
) -> Optional[Dict[str, Any]]:
    """
    Authenticate user with Google OAuth2
    
    Args:
        db: Database session
        authorization_code: OAuth2 authorization code from Google
        redirect_uri: Redirect URI used in the OAuth flow
        
    Returns:
        dict with user and token info, or None if authentication fails
    """
    try:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            error_log(
                action="login_with_google",
                function_name="login_with_google",
                file_name="oauth2_service.py",
                error="Google OAuth credentials not configured"
            )
            return None

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": authorization_code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )

            if token_response.status_code != 200:
                error_log(
                    action="login_with_google",
                    function_name="login_with_google",
                    file_name="oauth2_service.py",
                    error=f"Token exchange failed: {token_response.text}",
                    status_code=token_response.status_code
                )
                return None

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                error_log(
                    action="login_with_google",
                    function_name="login_with_google",
                    file_name="oauth2_service.py",
                    error="No access token in response",
                    response=token_data
                )
                return None

            user_info_response = await client.get(
                GOOGLE_USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if user_info_response.status_code != 200:
                error_log(
                    action="login_with_google",
                    function_name="login_with_google",
                    file_name="oauth2_service.py",
                    error=f"Failed to fetch user info: {user_info_response.text}",
                    status_code=user_info_response.status_code
                )
                return None

            user_info = user_info_response.json()
            email = user_info.get("email")
            name = user_info.get("name")
            google_id = user_info.get("id")

            if not email:
                error_log(
                    action="login_with_google",
                    function_name="login_with_google",
                    file_name="oauth2_service.py",
                    error="No email in user info",
                    user_info=user_info
                )
                return None

            user = await _get_user_by_email(db, email)

            if not user:
                user = await create_user(
                    db=db,
                    email=email,
                    password=None,
                    username=None,
                    name=name,
                    role="user"
                )
                info_log(
                    action="login_with_google",
                    status="user_created",
                    user_id=user.id,
                    email=email
                )

            oauth_token = await create_oauth_token(db, user.id)

            info_log(
                action="login_with_google",
                status="success",
                user_id=user.id,
                email=email
            )

            return {
                "user": user,
                "access_token": oauth_token.access_token,
                "refresh_token": oauth_token.refresh_token,
                "token_type": oauth_token.token_type,
                "expires_at": oauth_token.expires_at
            }

    except Exception as e:
        error_log(
            action="login_with_google",
            function_name="login_with_google",
            file_name="oauth2_service.py",
            error=str(e)
        )
        return None


async def login_with_facebook(
    db: AsyncSession,
    authorization_code: str,
    redirect_uri: str
) -> Optional[Dict[str, Any]]:
    """
    Authenticate user with Facebook OAuth2
    
    Args:
        db: Database session
        authorization_code: OAuth2 authorization code from Facebook
        redirect_uri: Redirect URI used in the OAuth flow
        
    Returns:
        dict with user and token info, or None if authentication fails
    """
    try:
        if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
            error_log(
                action="login_with_facebook",
                function_name="login_with_facebook",
                file_name="oauth2_service.py",
                error="Facebook OAuth credentials not configured"
            )
            return None

        async with httpx.AsyncClient() as client:
            token_response = await client.get(
                FACEBOOK_TOKEN_URL,
                params={
                    "client_id": settings.FACEBOOK_APP_ID,
                    "client_secret": settings.FACEBOOK_APP_SECRET,
                    "redirect_uri": redirect_uri,
                    "code": authorization_code
                }
            )

            if token_response.status_code != 200:
                error_log(
                    action="login_with_facebook",
                    function_name="login_with_facebook",
                    file_name="oauth2_service.py",
                    error=f"Token exchange failed: {token_response.text}",
                    status_code=token_response.status_code
                )
                return None

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                error_log(
                    action="login_with_facebook",
                    function_name="login_with_facebook",
                    file_name="oauth2_service.py",
                    error="No access token in response",
                    response=token_data
                )
                return None

            user_info_response = await client.get(
                FACEBOOK_USER_INFO_URL,
                params={
                    "access_token": access_token,
                    "fields": "id,name,email"
                }
            )

            if user_info_response.status_code != 200:
                error_log(
                    action="login_with_facebook",
                    function_name="login_with_facebook",
                    file_name="oauth2_service.py",
                    error=f"Failed to fetch user info: {user_info_response.text}",
                    status_code=user_info_response.status_code
                )
                return None

            user_info = user_info_response.json()
            email = user_info.get("email")
            name = user_info.get("name")
            facebook_id = user_info.get("id")

            if not email:
                error_log(
                    action="login_with_facebook",
                    function_name="login_with_facebook",
                    file_name="oauth2_service.py",
                    error="No email in user info",
                    user_info=user_info
                )
                return None

            user = await _get_user_by_email(db, email)

            if not user:
                user = await create_user(
                    db=db,
                    email=email,
                    password=None,
                    username=None,
                    name=name,
                    role="user"
                )
                info_log(
                    action="login_with_facebook",
                    status="user_created",
                    user_id=user.id,
                    email=email
                )

            oauth_token = await create_oauth_token(db, user.id)

            info_log(
                action="login_with_facebook",
                status="success",
                user_id=user.id,
                email=email
            )

            return {
                "user": user,
                "access_token": oauth_token.access_token,
                "refresh_token": oauth_token.refresh_token,
                "token_type": oauth_token.token_type,
                "expires_at": oauth_token.expires_at
            }

    except Exception as e:
        error_log(
            action="login_with_facebook",
            function_name="login_with_facebook",
            file_name="oauth2_service.py",
            error=str(e)
        )
        return None
