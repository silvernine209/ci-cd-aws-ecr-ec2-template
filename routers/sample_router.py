from fastapi import APIRouter
from logic.sample_logic import get_welcome_message

router = APIRouter()

@router.get("/hello")
async def hello_endpoint():
    """
    Sample endpoint that calls backend logic.
    """
    data = get_welcome_message()
    return data
