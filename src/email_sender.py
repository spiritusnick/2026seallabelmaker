"""
Email Sender Module
Sends generated fulfillment sticker PDFs via email using SMTP
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from dotenv import load_dotenv


class EmailSender:
    """Handles sending emails with PDF attachments via SMTP"""

    def __init__(self):
        """Load email configuration from environment variables"""
        # Load env.env from parent directory
        env_path = os.path.join(os.path.dirname(__file__), '..', 'env.env')
        load_dotenv(env_path)

        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_to = os.getenv("EMAIL_TO", "").split(",")
        self.email_subject_template = os.getenv("EMAIL_SUBJECT", "Daily Fulfillment Stickers - {date}")

        # Validate required configuration
        if not self.email_from or not self.email_password:
            raise ValueError("EMAIL_FROM and EMAIL_PASSWORD must be set in env.env")

        if not self.email_to or self.email_to == ['']:
            raise ValueError("EMAIL_TO must be set in env.env")

    def send_pdf(self, pdf_path, order_count=0, additional_info=""):
        """
        Send the PDF file via email

        Args:
            pdf_path: Path to the PDF file to send
            order_count: Number of orders processed (for email body)
            additional_info: Additional information to include in email body

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Verify PDF file exists
            if not os.path.exists(pdf_path):
                print(f"Error: PDF file not found at {pdf_path}")
                return False

            # Extract date from filename or use current date
            pdf_filename = os.path.basename(pdf_path)
            today = datetime.now().strftime("%Y-%m-%d")

            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ", ".join(self.email_to)
            msg['Subject'] = self.email_subject_template.format(date=today)

            # Create email body
            body = self._create_email_body(today, order_count, pdf_filename, additional_info)
            msg.attach(MIMEText(body, 'html'))

            # Attach PDF file
            with open(pdf_path, 'rb') as pdf_file:
                pdf_attachment = MIMEApplication(pdf_file.read(), _subtype="pdf")
                pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
                msg.attach(pdf_attachment)

            # Send email
            print(f"\n[Email] Connecting to {self.smtp_server}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)

            print(f"[Email] Successfully sent to: {', '.join(self.email_to)}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("Error: Email authentication failed. Check EMAIL_FROM and EMAIL_PASSWORD in env.env")
            return False
        except smtplib.SMTPException as e:
            print(f"Error: SMTP error occurred: {str(e)}")
            return False
        except Exception as e:
            print(f"Error: Failed to send email: {str(e)}")
            return False

    def _create_email_body(self, date, order_count, filename, additional_info):
        """
        Create HTML email body

        Args:
            date: Date string
            order_count: Number of orders processed
            filename: Name of the attached PDF file
            additional_info: Additional information to include

        Returns:
            str: HTML formatted email body
        """
        sticker_text = "sticker" if order_count == 1 else "stickers"

        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2c3e50;">Daily Fulfillment Stickers - {date}</h2>
                <p>Hello,</p>
                <p>Attached are today's fulfillment stickers for Spiritus Coffee Co.</p>

                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                    <strong>Summary:</strong><br>
                    • Orders processed: <strong>{order_count}</strong><br>
                    • Stickers generated: <strong>{order_count} {sticker_text}</strong><br>
                    • File: <strong>{filename}</strong>
                </div>
        """

        if additional_info:
            body += f"""
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <strong>Additional Information:</strong><br>
                    {additional_info}
                </div>
            """

        body += """
                <p><strong>Instructions:</strong></p>
                <ul>
                    <li>Print the attached PDF on Avery 5160 label sheets</li>
                    <li>Each line item gets its own sticker</li>
                    <li>Orders marked <strong style="color: red;">SHIP</strong> require shipping labels</li>
                    <li>Other orders are for local delivery</li>
                </ul>

                <p style="color: #6c757d; font-size: 0.9em; margin-top: 30px;">
                    This is an automated message from the Spiritus Coffee Fulfillment System.<br>
                    Generated on """ + datetime.now().strftime("%Y-%m-%d at %I:%M %p") + """
                </p>
            </body>
        </html>
        """

        return body


def main():
    """Test the email sender functionality"""
    print("=== Email Sender Test ===\n")

    try:
        sender = EmailSender()
        print(f"Configuration loaded:")
        print(f"  SMTP Server: {sender.smtp_server}:{sender.smtp_port}")
        print(f"  From: {sender.email_from}")
        print(f"  To: {', '.join(sender.email_to)}")
        print(f"  Subject Template: {sender.email_subject_template}")

        # For testing, you would need an actual PDF file
        # Uncomment below to test with a real PDF
        # test_pdf = "output/fulfillment-stickers-2025-01-15.pdf"
        # if os.path.exists(test_pdf):
        #     success = sender.send_pdf(test_pdf, order_count=5, additional_info="Test email")
        #     if success:
        #         print("\nTest email sent successfully!")
        #     else:
        #         print("\nTest email failed to send.")
        # else:
        #     print(f"\nTest PDF not found at {test_pdf}")

    except Exception as e:
        print(f"Error during test: {str(e)}")


if __name__ == "__main__":
    main()
