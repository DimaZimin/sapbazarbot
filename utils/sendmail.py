import smtplib, ssl


class MailManager:

    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.context = ssl.create_default_context()

    @staticmethod
    def message_to_sent(body: str, category: str, subject: str = None, name: str = None) -> str:
        if subject and name:
            return f"Subject: {subject} in {category}\n Hello, {name}!\n{body}"
        elif subject:
            return f"Subject: {subject} in {category}\n Hello, user!{body}"
        elif name:
            return f"Hello, {name}!\n{body}"
        else:
            return body

    def send_mass_mail(self, receivers: list, message: str, subject: str = None):
        emails_sent = 0
        try:
            with smtplib.SMTP_SSL(self.host, self.port, context=self.context) as server:
                server.login(self.user, self.password)
                for receiver in receivers:
                    message_to_sent = self.message_to_sent(message, subject, receiver[0])
                    try:
                        server.sendmail(self.user, receiver[1], message_to_sent)
                        emails_sent += 1
                    except Exception as e:
                        print("Exception: ", e)

        except Exception as e:
            print('Exception: ', e)
        finally:
            print('Emails sent: ', emails_sent)

    @staticmethod
    def create_url_for_project(project_id, slug):
        return f"https://projects.sapbazar.com/projects/{project_id}/{slug}"
