import django.test
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test.client import Client

from settool_common.models import Semester
from tutors.models import Tutor


class CSVTest(django.test.TestCase):
    fixtures = ["Tutors.json"]

    def setUp(self) -> None:
        # setup User
        self.client = Client()

        self.user = get_user_model().objects.create_user(  # nosec: this is a unittest
            username="testuser",
            password="12345",
            is_superuser=True,
        )
        self.client.force_login(self.user)
        self.csv_header = b"last_name,first_name,subject,matriculation_number,birthday\r\n"

    def test_csv_tutor_export(self):
        expected_tutors = Tutor.objects.filter(
            semester=Semester.objects.get(pk=2),  # pk=2 ^= SS 21
        ).order_by(
            "last_name",
            "first_name",
        )
        res: HttpResponse = self.client.get("/tutors/tutor/export/csv/")
        self.assertEqual(res.get("content-type"), "text/csv")
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
        res: HttpResponse = self.client.get(f"/tutors/tutor/export/csv/{Tutor.STATUS_INACTIVE}")
        self.assertEqual(res.get("content-type"), "text/csv")
        self.assertEqual(res.content, self.csv_header)

    def test_csv_tutor_export_filtering_declined(self):
        expected_tutors = Tutor.objects.filter(
            semester=Semester.objects.get(pk=2),  # pk=2 ^= SS 21
            status=Tutor.STATUS_DECLINED,
        ).order_by(
            "last_name",
            "first_name",
        )
        res: HttpResponse = self.client.get(f"/tutors/tutor/export/csv/{Tutor.STATUS_DECLINED}")
        self.assertEqual(res.get("content-type"), "text/csv")
        content = res.content
        self.assertGreater(len(content), len(self.csv_header))
        content = str(content.strip(self.csv_header), "utf-8").split("\r\n")
        for i, expected_tutor in enumerate(expected_tutors):
            self.assertEqual(
                f"{expected_tutor.last_name},{expected_tutor.first_name},{expected_tutor.subject},"
                f"{expected_tutor.matriculation_number},{expected_tutor.birthday}",
                content[i],
            )
