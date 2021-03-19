import random

from django.utils.datetime_safe import datetime

from settool_common.models import CourseBundle, current_semester, Semester, Subject
from tutors.models import Tutor


def create_tutor_fixture_state():
    course_bundle_mathe = CourseBundle.objects.create(name="Mathe", name_de="Mathematics", name_en="Mathematik")
    course_bundle_info = CourseBundle.objects.create(name="Info", name_de="Informatics", name_en="Informatik")
    subject1 = Subject.objects.create(
        degree=Subject.BACHELOR,
        subject="Info",
        subject_de="Informathik",
        subject_en="Informathics",
        course_bundle=course_bundle_info,
    )
    subject2 = Subject.objects.create(
        degree=Subject.MASTER,
        subject="Mathe",
        subject_de="Mathemathik",
        subject_en="mathemathics",
        course_bundle=course_bundle_mathe,
    )
    semester1, semester2 = generate_semesters()

    for i in range(20):
        tutor = Tutor(  # nosec: this is a fixture
            semester=semester1 if i % 2 == 0 else semester2,
            first_name=f"Firstname_{i}",
            last_name=f"Lastname_{i}",
            email=f"{i}@test.com",
            subject=subject1 if random.randint(0, 1) == 0 else subject2,
            tshirt_size=Tutor.TSHIRT_SIZES[i % len(Tutor.TSHIRT_SIZES)][0],
            tshirt_girls_cut=random.randint(0, 1) == 0,
            status=Tutor.STATUS_ACCEPTED if i >= 5 else Tutor.STATUS_DECLINED,
            matriculation_number=f"{i:02d}",
            birthday=datetime.today(),
        )
        tutor.save()


def generate_semesters():
    semester1 = Semester(semester="WS", year=2019)  # legacy data that should not be shown
    semester1.save()
    semester2 = current_semester()
    semester2.save()
    return semester1, semester2
