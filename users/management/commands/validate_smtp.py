import smtplib
import ssl
from email.message import EmailMessage

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Validate SMTP connection using settings. Optionally send a test email with --to.'

    def add_arguments(self, parser):
        parser.add_argument('--to', help='Send a test email to this address after validating connection')
        parser.add_argument('--subject', help='Subject for test email', default='SIMS SMTP validation')
        parser.add_argument('--body', help='Body for test email', default='This is a test email sent by the SIMS validate_smtp command.')
        parser.add_argument('--timeout', help='Socket timeout in seconds', type=int, default=10)

    def handle(self, *args, **options):
        backend = getattr(settings, 'EMAIL_BACKEND', '')
        host = getattr(settings, 'EMAIL_HOST', '')
        port = getattr(settings, 'EMAIL_PORT', None)
        user = getattr(settings, 'EMAIL_HOST_USER', '')
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        use_tls = getattr(settings, 'EMAIL_USE_TLS', False)
        use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
        timeout = options.get('timeout') or 10

        self.stdout.write(self.style.MIGRATE_HEADING('SMTP Validation'))
        self.stdout.write(f'Configured EMAIL_BACKEND = {backend}')

        if not host or not port:
            self.stdout.write(self.style.WARNING('EMAIL_HOST or EMAIL_PORT not configured. Nothing to validate.'))
            return

        try:
            port = int(port)
        except Exception:
            self.stdout.write(self.style.ERROR(f'Invalid EMAIL_PORT: {port}'))
            return

        context = ssl.create_default_context()

        try:
            if use_ssl:
                self.stdout.write(f'Connecting using SMTP_SSL to {host}:{port} ...')
                server = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
            else:
                self.stdout.write(f'Connecting using SMTP to {host}:{port} ...')
                server = smtplib.SMTP(host, port, timeout=timeout)

            server.set_debuglevel(0)
            # greet
            server.ehlo()

            if use_tls and not use_ssl:
                self.stdout.write('Starting TLS ...')
                server.starttls(context=context)
                server.ehlo()

            if user and password:
                self.stdout.write('Attempting to authenticate ...')
                try:
                    server.login(user, password)
                except smtplib.SMTPAuthenticationError as e:
                    self.stdout.write(self.style.ERROR(f'Authentication failed: {e}'))
                    server.quit()
                    return

            # NOOP to confirm server responsiveness
            code, resp = server.noop()
            self.stdout.write(self.style.SUCCESS(f'SMTP server responded: {code} {resp}'))

            # Optionally send test email
            to_addr = options.get('to')
            if to_addr:
                self.stdout.write(f'Sending test email to {to_addr} ...')
                msg = EmailMessage()
                msg['Subject'] = options.get('subject')
                msg['From'] = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')
                msg['To'] = to_addr
                msg.set_content(options.get('body'))
                try:
                    server.send_message(msg)
                    self.stdout.write(self.style.SUCCESS('Test email accepted by SMTP server (check recipient inbox/spam).'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to send test email: {e}'))

            server.quit()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to validate SMTP connection: {e}'))
            return

        self.stdout.write(self.style.SUCCESS('SMTP validation completed.'))
