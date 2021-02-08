from typing import Any, Dict, List, Optional

from django.core import mail
from django.core.mail import EmailMessage
from django.template import Context, Template
from django.test import TestCase

import settool_common.fixtures.showroom_fixture
import settool_common.models as common_models


def assert_outbox_equal_exept_ordering(self: Any, expected: List[Dict[str, str]]) -> None:
    outbox: List[EmailMessage] = mail.outbox
    self.assertEqual(len(outbox), len(expected))
    for email in outbox:
        sent_email = {
            "subject": email.subject.strip(),
            "text": email.body.strip(),
            "recipients": email.from_email.strip(),
        }
        self.assertIn(sent_email, expected)


def assert_stripped_equal(self: Any, first: str, second: str, msg: Optional[str] = None) -> None:
    self.assertEqual(first.strip(), second.strip(), msg)


class SendEmailTemplated(TestCase):
    context: Context = Context({"template1": "template1 was inserted here"})

    @classmethod
    def setUpTestData(cls) -> None:
        common_models.Mail.objects.create(
            sender=common_models.Mail.SET,
            subject="hi",
            text="{{ template1 }} abcd",
        )
        common_models.Mail.objects.create(
            sender=common_models.Mail.SET,
            subject="{{ template1 }} ho",
            text="abcd",
        )

    def setUp(self) -> None:
        mail.outbox.clear()

    def test_get_mail(self):
        """check if the Mail.get_mail method works correctly with an filled template"""

        mail_object: common_models.Mail
        for mail_object in common_models.Mail.objects.all():
            subject, text, from_email_adress = mail_object.get_mail(self.context)
            assert_stripped_equal(self, subject, Template(mail_object.subject).render(self.context))
            assert_stripped_equal(self, text, Template(mail_object.text).render(self.context))
            assert_stripped_equal(
                self,
                from_email_adress,
                Template(mail_object.sender).render(self.context),
            )

    def test_send_mail(self):
        """check if the Mail.send_mail method works correctly with an filled template"""

        mail_object: common_models.Mail
        for mail_object in common_models.Mail.objects.all():
            self.assertTrue(mail_object.send_mail(self.context, "abc@gmail.com"))
            expected = [
                {
                    "subject": Template(mail_object.subject).render(self.context),
                    "text": Template(mail_object.text).render(self.context),
                    "recipients": Template(mail_object.sender).render(self.context),
                },
            ]
            assert_outbox_equal_exept_ordering(self, expected)
            mail.outbox.clear()


class SendEmailNoTemplate(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        settool_common.fixtures.showroom_fixture.generate_common_mails()

    def setUp(self) -> None:
        mail.outbox.clear()

    def test_get_mail(self):
        """check if the Mail.get_mail method works correctly with an empty template"""

        mail_object: common_models.Mail
        for mail_object in common_models.Mail.objects.all()[:5]:
            subject, text, from_email_adress = mail_object.get_mail(Context({}))
            assert_stripped_equal(self, subject, mail_object.subject)
            assert_stripped_equal(self, text, mail_object.text)
            assert_stripped_equal(self, from_email_adress, mail_object.sender)

    def test_send_mail(self):
        """check if the Mail.send_mail method works correctly with an empty template"""

        mail_object: common_models.Mail
        for mail_object in common_models.Mail.objects.all()[:5]:
            self.assertTrue(mail_object.send_mail(Context({}), "abc@gmail.com"))
            expected = [
                {
                    "subject": mail_object.subject.strip(),
                    "text": mail_object.text.strip(),
                    "recipients": mail_object.sender.strip(),
                },
            ]
            assert_outbox_equal_exept_ordering(
                self,
                expected,
            )
            mail.outbox.clear()
