import smtplib, ssl


class MailManager:

    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.context = ssl.create_default_context()

    @staticmethod
    def message_to_sent(url: str, category: str, request_id, name: str) -> str:
        return f"Subject: New sap assistance request nr{request_id} in {category}.\n" \
               f"Dear {name}! There has been posted new SAP assistance request in SAP {category}" \
               f"and your experience is needed. Please help our colleague if you can. " \
               f"The project information is available by this link: {url}"

    def send_mass_mail(self, receivers: list, url: str, category: str, request_id: str):
        emails_sent = 0
        try:
            with smtplib.SMTP_SSL(self.host, self.port, context=self.context) as server:
                server.login(self.user, self.password)
                for receiver in receivers:
                    message_to_sent = self.message_to_sent(url,
                                                           category=category,
                                                           request_id=request_id,
                                                           name=receiver[0])
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
