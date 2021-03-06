import re

import django.test
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test.client import Client
from django_tex.core import compile_template_to_pdf

from settool_common.models import Semester
from settool_common.settings import SEMESTER_SESSION_KEY
from tutors.models import Task, Tutor


def remove_unique_fields_from_pdf(initial_pdf):
    pdf = re.sub(b"/CreationDate .+\n", b"", initial_pdf)
    pdf = re.sub(b"/ModDate .+\n", b"", pdf)
    return re.sub(b"/ID .+\n", b"", pdf)


def get_mocked_logged_in_client():
    client = Client()

    user = get_user_model().objects.create_user(  # nosec: this is a unittest
        username="testuser",
        password="12345",
        is_superuser=True,
    )
    client.force_login(user)
    # reason the sesson has to be put into a variable:
    # https://stackoverflow.com/questions/7502116/how-to-use-session-in-testcase-in-django/37307406#37307406
    session = client.session
    session[SEMESTER_SESSION_KEY] = 2  # pk=2 ^= SS 21
    session.save()
    return client


def assert_pdf_equal(self, expected_pdf, provided_pdf):
    self.assertEqual(
        remove_unique_fields_from_pdf(expected_pdf),
        remove_unique_fields_from_pdf(provided_pdf),
        "The PDF does not look as expected",
    )


class TutorExportTest(django.test.TestCase):
    fixtures = ["Tutors.json"]

    def setUp(self):
        self.client = get_mocked_logged_in_client()
        self.csv_header = b"last_name,first_name,subject,matriculation_number,birthday\r\n"

    def test_csv_tutor_export(self):
        expected_tutors = Tutor.objects.filter(semester=Semester.objects.get(pk=2)).order_by(  # pk=2 ^= SS 21
            "last_name",
            "first_name",
        )
        res: HttpResponse = self.client.get("/tutors/tutor/export/csv/")
        self.assertEqual("text/csv", res.get("content-type"))
        content = res.content
        self.assertGreater(len(content), len(self.csv_header))
        content = str(content.strip(self.csv_header), "utf-8").split("\r\n")
        for i, expected_tutor in enumerate(expected_tutors):
            self.assertEqual(
                f"{expected_tutor.last_name},{expected_tutor.first_name},{expected_tutor.subject},"
                f"{expected_tutor.matriculation_number},{expected_tutor.birthday}",
                content[i],
            )

    def test_csv_tutor_export_no_data(self):
        res: HttpResponse = self.client.get(f"/tutors/tutor/export/csv/{Tutor.STATUS_INACTIVE}/")
        self.assertEqual("text/csv", res.get("content-type"))
        self.assertEqual(self.csv_header, res.content)

    def test_csv_tutor_export_filtering_declined(self):
        expected_tutors = Tutor.objects.filter(
            semester=Semester.objects.get(pk=2),  # pk=2 ^= SS 21
            status=Tutor.STATUS_DECLINED,
        ).order_by(
            "last_name",
            "first_name",
        )
        res: HttpResponse = self.client.get(f"/tutors/tutor/export/csv/{Tutor.STATUS_DECLINED}/")
        self.assertEqual("text/csv", res.get("content-type"))
        content = res.content
        self.assertGreater(len(content), len(self.csv_header))
        content = str(content.strip(self.csv_header), "utf-8").split("\r\n")
        for i, expected_tutor in enumerate(expected_tutors):
            self.assertEqual(
                f"{expected_tutor.last_name},{expected_tutor.first_name},{expected_tutor.subject},"
                f"{expected_tutor.matriculation_number},{expected_tutor.birthday}",
                content[i],
            )

    def test_tshirt_tutor_export_no_data(self):
        expected_tutors = Tutor.objects.filter(
            semester=Semester.objects.get(pk=2),  # pk=2 ^= SS 21
            status=Tutor.STATUS_EMPLOYEE,
        ).order_by(
            "last_name",
            "first_name",
        )
        expected_context = {"tutors": expected_tutors}
        expected_pdf = compile_template_to_pdf("tutors/tex/tshirts.tex", expected_context)
        res: HttpResponse = self.client.get(f"/tutors/tutor/export/tshirt/{Tutor.STATUS_EMPLOYEE}/")
        self.assertEqual("application/pdf", res.get("content-type"))
        assert_pdf_equal(self, expected_pdf, res.content)

    def test_tshirt_tutor_export(self):
        expected_tutors = Tutor.objects.filter(semester=Semester.objects.get(pk=2)).order_by(  # pk=2 ^= SS 21
            "last_name",
            "first_name",
        )
        expected_context = {"tutors": expected_tutors}
        expected_pdf = compile_template_to_pdf("tutors/tex/tshirts.tex", expected_context)
        res: HttpResponse = self.client.get("/tutors/tutor/export/tshirt/")
        self.assertEqual("application/pdf", res.get("content-type"))
        assert_pdf_equal(self, expected_pdf, res.content)

    def test_tshirt_tutor_export_filtering_declined(self):
        expected_tutors = Tutor.objects.filter(
            semester=Semester.objects.get(pk=2),  # pk=2 ^= SS 21
            status=Tutor.STATUS_DECLINED,
        ).order_by(
            "last_name",
            "first_name",
        )
        expected_context = {"tutors": expected_tutors}
        expected_pdf = compile_template_to_pdf("tutors/tex/tshirts.tex", expected_context)
        res: HttpResponse = self.client.get(f"/tutors/tutor/export/tshirt/{Tutor.STATUS_DECLINED}/")
        self.assertEqual("application/pdf", res.get("content-type"))
        assert_pdf_equal(self, expected_pdf, res.content)

    def test_pdf_tutor_export_no_data(self):
        expected_tutors = Tutor.objects.filter(
            semester=Semester.objects.get(pk=2),  # pk=2 ^= SS 21
            status=Tutor.STATUS_EMPLOYEE,
        ).order_by(
            "last_name",
            "first_name",
        )
        expected_context = {"tutors": expected_tutors}
        expected_pdf = compile_template_to_pdf("tutors/tex/tutors.tex", expected_context)
        res: HttpResponse = self.client.get(f"/tutors/tutor/export/pdf/{Tutor.STATUS_EMPLOYEE}/")
        self.assertEqual("application/pdf", res.get("content-type"))
        assert_pdf_equal(self, expected_pdf, res.content)

    def test_pdf_tutor_export(self):
        expected_tutors = Tutor.objects.filter(semester=Semester.objects.get(pk=2)).order_by(  # pk=2 ^= SS 21
            "last_name",
            "first_name",
        )
        expected_context = {"tutors": expected_tutors}
        expected_pdf = compile_template_to_pdf("tutors/tex/tutors.tex", expected_context)
        res: HttpResponse = self.client.get("/tutors/tutor/export/pdf/")
        self.assertEqual("application/pdf", res.get("content-type"))
        assert_pdf_equal(self, expected_pdf, res.content)

    def test_pdf_tutor_export_filtering_declined(self):
        expected_tutors = Tutor.objects.filter(
            semester=Semester.objects.get(pk=2),  # pk=2 ^= SS 21
            status=Tutor.STATUS_DECLINED,
        ).order_by(
            "last_name",
            "first_name",
        )
        expected_context = {"tutors": expected_tutors}
        expected_pdf = compile_template_to_pdf("tutors/tex/tutors.tex", expected_context)
        res: HttpResponse = self.client.get(f"/tutors/tutor/export/pdf/{Tutor.STATUS_DECLINED}/")
        self.assertEqual("application/pdf", res.get("content-type"))
        assert_pdf_equal(self, expected_pdf, res.content)


class TaskExportTest(django.test.TestCase):
    fixtures = ["Tutors.json"]

    def setUp(self):
        self.client = get_mocked_logged_in_client()

    def test_pdf_export_task_no_data(self):
        self.task_pdf_generation("3cd2b4b0-c36f-4348-8a93-b3bb72029f46")

    def test_pdf_export_task(self):
        self.task_pdf_generation("3cd2b4b0-c36f-4348-8a93-b3bb72029f47")

    def task_pdf_generation(self, private_key):
        expected_task = Task.objects.get(pk=private_key)
        expected_tutors = expected_task.tutors.order_by("last_name", "first_name")
        expected_context = {"task": expected_task, "tutors": expected_tutors}
        expected_pdf = compile_template_to_pdf("tutors/tex/task.tex", expected_context)
        res: HttpResponse = self.client.get(f"/tutors/task/export/pdf/{private_key}/")
        self.assertEqual("application/pdf", res.get("content-type"))
        assert_pdf_equal(self, expected_pdf, res.content)
