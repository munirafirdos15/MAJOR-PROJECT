import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from app.core.config import settings


class EmailService:
    def __init__(self):
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.brevo_api_key

        self.client = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    async def send_email_verification(
        self,
        recipient_email: str,
        recipient_name: str,
        verification_token: str,
    ) -> None:

        verification_url = (
            f"{settings.frontend_url}"
            f"/verify-email?token={verification_token}"
        )

        email = sib_api_v3_sdk.SendSmtpEmail(
            sender=sib_api_v3_sdk.SendSmtpEmailSender(
                email=settings.brevo_sender_email,
                name=settings.brevo_sender_name,
            ),
            to=[
                sib_api_v3_sdk.SendSmtpEmailTo(
                    email=recipient_email,
                    name=recipient_name,
                )
            ],
            subject="Verify your email address",
            html_content=f"""
            <h2>Verify your email address</h2>
            <p>Hello {recipient_name},</p>
            <p>
                Thank you for registering with the
                Legal Document Intelligence System.
            </p>
            <p>
                <a href="{verification_url}">
                    Verify Email
                </a>
            </p>
            <p>
                This verification link will expire in 24 hours.
            </p>
            """,
        )

        try:
            self.client.send_transac_email(email)
        except ApiException as ex:
            raise RuntimeError(
                "Unable to send verification email"
            ) from ex