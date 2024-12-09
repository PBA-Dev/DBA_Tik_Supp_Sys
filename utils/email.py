import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotifier:
    def __init__(self):
        self.sender_email = "support@yourdomain.com"
        self.smtp_server = "smtp.yourdomain.com"
        self.smtp_port = 587

    def send_notification(self, recipient, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                # server.login(username, password)  # Add credentials when needed
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

    def notify_ticket_created(self, ticket, assignee_email):
        subject = f"New Ticket Created: {ticket['title']}"
        body = f"""
        <h2>New Support Ticket</h2>
        <p><strong>Title:</strong> {ticket['title']}</p>
        <p><strong>Priority:</strong> {ticket['priority']}</p>
        <p><strong>Description:</strong> {ticket['description']}</p>
        """
        self.send_notification(assignee_email, subject, body)

    def notify_ticket_updated(self, ticket, user_email):
        subject = f"Ticket Updated: {ticket['title']}"
        body = f"""
        <h2>Ticket Update</h2>
        <p><strong>Title:</strong> {ticket['title']}</p>
        <p><strong>Status:</strong> {ticket['status']}</p>
        <p><strong>Priority:</strong> {ticket['priority']}</p>
        """
        self.send_notification(user_email, subject, body)
