from django.core import mail
from django.template import Context
from django.template import Template
from django.test import TestCase

import settool_common.fixtures.showroom_fixture
import settool_common.models as common_models
from settool_common.fixtures.test_fixture import generate_semesters


def assert_outbox_equal_exept_ordering(self, expected):
    outbox = mail.outbox
    self.assertEqual(len(outbox), len(expected))
    for email in outbox:
        sent_email = {"subject": email.subject, "text": email.body, "recipients": email.from_email}
        self.assertIn(sent_email, expected)


class SendEmailTemplated(TestCase):
    context = Context({"template1": "template1 was inserted here"})

    @classmethod
    def setUpTestData(cls) -> None:
        semester1, semester2 = generate_semesters()
        common_models.Mail.objects.create(
            semester=semester1,
            sender=common_models.Mail.SET,
            subject="hi",
            text="{{ template1 }} abcd",
        )
        common_models.Mail.objects.create(
            semester=semester2,
            sender=common_models.Mail.SET,
            subject="{{ template1 }} ho",
            text="abcd",
        )

    def setUp(self) -> None:
        mail.outbox.clear()

    def test_get_mail(self):
        """check if the settool_common.models.Mail.get_mail method
        works correctly with an filled template"""

        mail_object: common_models.Mail
        for mail_object in common_models.Mail.objects.all():
            subject, text, from_email_adress = mail_object.get_mail(self.context)
            self.assertEqual(subject, Template(mail_object.subject).render(self.context))
            self.assertEqual(text, Template(mail_object.text).render(self.context))
            self.assertEqual(from_email_adress, Template(mail_object.sender).render(self.context))

    def test_send_mail(self):
        """check if the settool_common.models.Mail.send_mail method
        works correctly with an filled template"""

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
        settool_common.fixtures.showroom_fixture.generate_common_mails(generate_semesters())

    def setUp(self) -> None:
        mail.outbox.clear()

    def test_get_mail(self):
        """check if the settool_common.models.Mail.get_mail method
        works correctly with an empty template"""

        mail_object: common_models.Mail
        for mail_object in common_models.Mail.objects.all()[:5]:
            subject, text, from_email_adress = mail_object.get_mail(Context({}))
            self.assertEqual(subject, mail_object.subject)
            self.assertEqual(text, mail_object.text)
            self.assertEqual(from_email_adress, mail_object.sender)

    def test_send_mail(self):
        """check if the settool_common.models.Mail.send_mail method
        works correctly with an empty template"""

        mail_object: common_models.Mail
        for mail_object in common_models.Mail.objects.all()[:5]:
            self.assertTrue(mail_object.send_mail(Context({}), "abc@gmail.com"))
            expected = [
                {
                    "subject": mail_object.subject,
                    "text": mail_object.text,
                    "recipients": mail_object.sender,
                },
            ]
            assert_outbox_equal_exept_ordering(
                self,
                expected,
            )
            mail.outbox.clear()
