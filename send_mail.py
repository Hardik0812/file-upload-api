from fastapi import BackgroundTasks, FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import BaseModel, EmailStr

app = FastAPI()

# Configure email settings
conf = ConnectionConfig(
    MAIL_USERNAME="c.hardik125@gmail.com",
    MAIL_PASSWORD="frzdeegakgsbluqu",
    MAIL_FROM="c.hardik125@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
)


# Pydantic model for email request
class EmailRequest(BaseModel):
    email: EmailStr


@app.post("/send-reset-link")
async def send_reset_link(request: EmailRequest, background_tasks: BackgroundTasks):
    # Create email content
    token = "your_generated_token"  # Replace with the actual token
    link = f"http://example.com/reset-password?token={token}"
    subject = "Password Reset"
    body = f"Hi,\n\nClick the link below to reset your password:\n{link}\n\nThank you."

    message = MessageSchema(
        subject=subject,
        recipients=[request.email],
        body=body,
        subtype="plain",
    )

    # Send email in the background
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
    return {"message": "Password reset link sent successfully"}
