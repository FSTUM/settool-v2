import random
from datetime import timedelta
from typing import Any, List, Optional, Set, Tuple

from django.core import mail
from django.core.mail import EmailMessage
from django.db.models import QuerySet
from django.db.models.query_utils import Q
from django.template import Context, Template
from django.test import TestCase
from django.utils import timezone
from django.utils.datetime_safe import date, datetime

import fahrt.models as fahrt_models
import guidedtours.models as tour_models
import settool_common.cron as cron
import settool_common.fixtures.showroom_fixture
import settool_common.models as common_models
import tutors.models as tutor_models


def serialise_outbox() -> Set[Tuple[str, str, str]]:
    outbox: List[EmailMessage] = mail.outbox
    res = set()
    for email in outbox:
        res.add((email.subject.strip(), email.body.strip(), email.from_email.strip()))
    outbox.clear()
    return res


def assert_stripped_equal(self: Any, first: str, second: str, msg: Optional[str] = None) -> None:
    self.assertEqual(first.strip(), second.strip(), msg)


class CronFahrt(TestCase):
    todatetime = timezone.make_aware(datetime.today())
    today: date = date.today()
    fahrt_obj: fahrt_models.Fahrt

    @classmethod
    def setUpTestData(cls) -> None:
        payment_mail = fahrt_models.FahrtMail.objects.create(
            sender=fahrt_models.FahrtMail.SET_FAHRT,
            subject="Payment_mail {{participant}}",
            text="Payment_mail_text",
        )
        reminder_email = fahrt_models.FahrtMail.objects.create(
            sender=fahrt_models.FahrtMail.SET_FAHRT,
            subject="Reminder_mail {{participant}}",
            text="Reminder_mail_text",
        )
        cls.fahrt_obj = fahrt_models.Fahrt.objects.create(
            semester=common_models.current_semester(),
            date=cls.today + timedelta(days=1),
            close_registration=cls.todatetime,
            open_registration=cls.todatetime,
            mail_reminder=reminder_email,
            reminder_tour_days_count=0,
            mail_payment_deadline=payment_mail,
            reminder_payment_deadline_days_count=0,
        )
        subject = common_models.Subject.objects.create(
            degree=common_models.Subject.MASTER,
            subject=common_models.Subject.OPERATIONS_RESEARCH,
        )
        for i in range(10):
            fahrt_models.Participant.objects.create(
                semester=common_models.current_semester(),
                gender=random.choice(fahrt_models.Participant.GENDER_CHOICES)[0],  # nosec: B311
                firstname=f"firstname {i}",
                surname=f"surname {i}",
                birthday=cls.today - timedelta(weeks=random.randint(1, 200)),  # nosec: B311
                email=f"a{i}@test.de",
                phone=f"+49 000 {i}",
                subject=subject,
                nutrition="normal",
                payment_deadline=date.today() + timedelta(days=1) if i % 2 == 0 else None,  # nosec: B311
                status="confirmed",
            )

    def _fahrt_helper(
        self,
        mail_obj: fahrt_models.FahrtMail,
        should_send_to: QuerySet[fahrt_models.Participant],
        meth: Any,
    ) -> None:
        for participant in should_send_to:
            mail_obj.send_mail_participant(participant)
        expected = serialise_outbox()
        meth(self.fahrt_obj.semester, self.today)
        curr = serialise_outbox()
        self.assertEqual(curr, expected)

    def test_fahrt_date_reminder(self):
        for days_until in range(-2, 4):
            self.fahrt_obj.reminder_tour_days_count = days_until
            self.fahrt_obj.save()
            days_until = max(days_until, 0)
            if self.today + timedelta(days=days_until) == self.fahrt_obj.date:
                should_send_to = fahrt_models.Participant.objects.all()
            else:
                should_send_to = fahrt_models.Participant.objects.none()
            self._fahrt_helper(self.fahrt_obj.mail_reminder, should_send_to, cron.fahrt_date_reminder)

    def test_fahrt_payment_reminder(self):
        for days_until in range(-2, 4):
            self.fahrt_obj.reminder_payment_deadline_days_count = days_until
            self.fahrt_obj.save()
            days_until = max(days_until, 0)
            lookup_day = self.today + timedelta(days=days_until)
            should_send_to = fahrt_models.Participant.objects.filter(
                Q(status="confirmed") & Q(payment_deadline=lookup_day),
            )
            self._fahrt_helper(self.fahrt_obj.mail_payment_deadline, should_send_to, cron.fahrt_payment_reminder)


class CronTutor(TestCase):
    todatetime = timezone.make_aware(datetime.today())
    today: date = date.today()
    setting: tutor_models.Settings

    @classmethod
    def setUpTestData(cls) -> None:
        mail_reminder = tutor_models.TutorMail.objects.create(
            sender=fahrt_models.FahrtMail.SET_TUTOR,
            subject="Reminder_mail {{tutor}}",
            text="Reminder_mail_text {{task}}",
        )
        cls.setting = tutor_models.Settings.objects.create(
            semester=common_models.current_semester(),
            close_registration=cls.todatetime,
            open_registration=cls.todatetime,
            mail_reminder=mail_reminder,
            reminder_tour_days_count=0,
        )
        subject = common_models.Subject.objects.create(
            degree=common_models.Subject.MASTER,
            subject=common_models.Subject.OPERATIONS_RESEARCH,
        )
        event = tutor_models.Event.objects.create(
            semester=common_models.current_semester(),
            name="enent",
            begin=cls.todatetime,
            end=cls.todatetime,
            meeting_point="-",
        )
        for i in range(2):
            tutor_models.Tutor.objects.create(
                semester=common_models.current_semester(),
                first_name=f"firstname {i}",
                last_name=f"surname {i}",
                email=f"a{i}@test.de",
                tshirt_size="L",
                tshirt_girls_cut=False,
                status=tutor_models.Tutor.STATUS_OPTIONS[i % len(tutor_models.Tutor.STATUS_OPTIONS)][0],
                subject=subject,
            )
        tutors = list(tutor_models.Tutor.objects.all())
        for i in range(10):
            task = tutor_models.Task.objects.create(
                semester=common_models.current_semester(),
                name=f"task {i}",
                begin=cls.todatetime,
                end=cls.todatetime,
                meeting_point="-",
                event=event,
            )
            for tutor in tutors:
                tutor_models.TutorAssignment.objects.create(
                    tutor=tutor,
                    task=task,
                )

    def setUp(self) -> None:
        mail.outbox.clear()

    def test_tutor_reminder(self):
        for days_until in range(-2, 4):
            self.setting.reminder_tour_days_count = days_until
            self.setting.save()
            days_until = max(days_until, 0)
            lookup_day = self.today + timedelta(days=days_until)

            task: tutor_models.Task
            for task in tutor_models.Task.objects.filter(
                Q(semester=common_models.current_semester())
                & Q(begin__day=lookup_day.day)  # begin is datetime
                & Q(begin__month=lookup_day.month)
                & Q(begin__year=lookup_day.year),
            ):
                tutor: tutor_models.Tutor
                for tutor in list(task.tutors.all()):
                    self.setting.mail_reminder.send_mail_task(tutor, task)
            expected = serialise_outbox()
            cron.tutor_reminder(common_models.current_semester(), self.today)
            curr = serialise_outbox()
            self.assertEqual(curr, expected)


class CronGuidedtour(TestCase):
    todatetime = timezone.make_aware(datetime.today())
    today: date = date.today()
    setting: tour_models.Setting

    @classmethod
    def setUpTestData(cls) -> None:
        mail_reminder = tour_models.TourMail.objects.create(
            sender=fahrt_models.FahrtMail.SET,
            subject="Reminder_mail {{participant}}",
            text="Reminder_mail_text",
        )
        cls.setting = tour_models.Setting.objects.create(
            semester=common_models.current_semester(),
            mail_reminder=mail_reminder,
            reminder_tour_days_count=0,
        )
        subject = common_models.Subject.objects.create(
            degree=common_models.Subject.MASTER,
            subject=common_models.Subject.OPERATIONS_RESEARCH,
        )
        for i in range(4):
            tour_models.Tour.objects.create(
                semester=common_models.current_semester(),
                name="tour today",
                date=cls.today + timedelta(days=i),
                capacity=10,
                open_registration=cls.todatetime,
                close_registration=cls.todatetime,
            )
        for tour in tour_models.Tour.objects.all():
            for i in range(10):
                tour_models.Participant.objects.create(
                    tour=tour,
                    firstname=f"firstname {i}",
                    surname=f"surname {i}",
                    email=f"a{i}@test.de",
                    phone=f"+49 000 {i}",
                    subject=subject,
                )

    def test_guidedtour_reminder(self):
        for days_until in range(-2, 4):
            days_until = max(days_until, 0)
            lookup_day = self.today + timedelta(days=days_until)
            tour: tour_models.Tour
            for tour in tour_models.Tour.objects.filter(
                Q(date__day=lookup_day.day)  # date is datetime
                & Q(date__month=lookup_day.month)
                & Q(date__year=lookup_day.year),
            ):
                participant: tour_models.Participant
                for participant in [
                    participant for participant in tour.participant_set.all() if participant.on_the_tour
                ]:
                    self.setting.mail_reminder.send_mail_participant(participant)
            expected = serialise_outbox()
            mail.outbox.clear()
            cron.guidedtour_reminder(self.setting.semester, self.today)
            self.assertEqual(serialise_outbox(), expected)


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

    def test_get_mail(self):
        """check if the Mail.get_mail method works correctly with an filled template"""

        mail_object: common_models.Mail
        for mail_object in common_models.Mail.objects.all():
            subject, text, from_email_adress = mail_object.get_mail(self.context)
            assert_stripped_equal(self, subject, Template(mail_object.subject).render(self.context))
            assert_stripped_equal(self, text, Template(mail_object.text).render(self.context))
            assert_stripped_equal(self, from_email_adress, Template(mail_object.sender).render(self.context))

    def test_send_mail(self):
        """check if the Mail.send_mail method works correctly with an filled template"""

        mail_object: common_models.Mail
        for mail_object in common_models.Mail.objects.all():
            self.assertTrue(mail_object.send_mail(self.context, "abc@gmail.com"))
            expected = {
                (
                    Template(mail_object.subject).render(self.context),
                    Template(mail_object.text).render(self.context),
                    Template(mail_object.sender).render(self.context),
                ),
            }
            self.assertEqual(serialise_outbox(), expected)


class SendEmailNoTemplate(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        settool_common.fixtures.showroom_fixture.generate_common_mails()

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
            expected = {(mail_object.subject.strip(), mail_object.text.strip(), mail_object.sender.strip())}
            self.assertEqual(serialise_outbox(), expected)
