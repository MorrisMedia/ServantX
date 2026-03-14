from fastapi import APIRouter, HTTPException, status
from schemas import ContactRequest
from services.email_service import send_contact_email

router = APIRouter(tags=["contact"])


@router.post("/contact")
async def submit_contact(data: ContactRequest):
    """
    Submit contact form and send email via SendGrid
    """
    try:
        result = send_contact_email(data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

