import random

from django.utils.datetime_safe import datetime

from settool_common.models import current_semester
from settool_common.models import Semester
from settool_common.models import Subject
from tutors.models import Tutor


def create_tutor_fixture_state():
    semester1 = Semester(semester="WS", year=2019)  # legacy data that should not be shown
    semester1.save()
    semester2 = current_semester()
    semester2.save()
    subject1 = Subject(degree=Subject.BACHELOR, subject=Subject.INFORMATICS)
    subject1.save()
    subject2 = Subject(degree=Subject.MASTER, subject=Subject.MATHEMATICS)
    subject2.save()

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
