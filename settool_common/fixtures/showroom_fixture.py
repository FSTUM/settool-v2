import random
from datetime import timedelta
from subprocess import run  # nosec: used for flushing the db
from typing import List

import django.utils.timezone
import lorem
from django.contrib.auth import get_user_model
from django.utils.datetime_safe import datetime

import bags.models
import fahrt.models
import guidedtours.models
import settool_common.models
import tutors.models
from settool_common.fixtures.test_fixture import generate_semesters


def showroom_fixture_state():  # nosec: this is only used in a fixture
    confirmation = input(
        "Do you really want to load the showroom fixture? (This will flush the database) [y/n]",
    )
    if confirmation.lower() != "y":
        return

    run(["python3", "manage.py", "flush", "--noinput"], check=True)

    # user
    superuser_frank = _generate_superuser_frank()

    # app settool-common
    common_semesters = generate_semesters()
    common_subjects = _generate_subjects()
    _generate_common_mails(common_semesters)

    # app bags
    _generate_companies(common_semesters)
    _generate_bags_mails(common_semesters)

    # app fahrt
    fahrt_data = _generate_fahrt_data()
    fahrt_participants = _generate_fahrt_participants(common_subjects, fahrt_data)
    _generate_log_entries(fahrt_participants, superuser_frank)
    _generate_fahrt_mails(common_semesters)

    # app guildedtours
    guildedtours_tours = _generate_guildedtours_tours(common_semesters)
    _generate_guildedtours_participants(common_subjects, guildedtours_tours)
    _generate_guildedtours_mails(common_semesters)

    # app tutors
    tutors_list = _generate_tutors(common_semesters, common_subjects)
    tutors_questions = _generate_questions(common_semesters)
    _generate_answers(tutors_questions, tutors_list)
    tutors_events = _generate_events(common_semesters, common_subjects)
    tutors_tasks = _generate_tasks(tutors_events, tutors_list, tutors_questions)
    _generate_tutor_setting()
    _generate_tutorassignment(tutors_list, tutors_tasks)
    # TODO tutors_mailtutortask
    # TODO tutors_subjecttutorcountassignment


def _generate_tutorassignment(tutors_list, tutors_tasks):  # nosec: this is only used in a fixture
    tutors_tutorassignment = []
    for tutor in tutors_list:
        for task in random.sample(tutors_tasks, random.choice((1, 1, 2))):
            tutors_tutorassignment.append(
                tutors.models.TutorAssignment.objects.create(
                    task=task,
                    tutor=tutor,
                ),
            )
    return tutors_tutorassignment


def _generate_tutor_setting():  # nosec: this is only used in a fixture
    all_mail_by_set_tutor = settool_common.models.Mail.objects.filter(
        sender=settool_common.models.Mail.SET_TUTOR,
    ).all()
    return tutors.models.Settings.objects.create(
        semester=settool_common.models.current_semester(),
        open_registration=django.utils.timezone.make_aware(datetime.today() - timedelta(days=20)),
        close_registration=django.utils.timezone.make_aware(datetime.today() + timedelta(days=20)),
        mail_registration=all_mail_by_set_tutor[0],
        mail_confirmed_place=all_mail_by_set_tutor[1],
        mail_waiting_list=all_mail_by_set_tutor[2],
        mail_declined_place=all_mail_by_set_tutor[3],
        mail_task=all_mail_by_set_tutor[4],
    )


def generate_random_birthday():  # nosec: this is only used in a fixture
    """
    :return: valid birthday that is 10..40 years in the past
    """
    random_number_of_days = random.randint(
        356 * 10,
        365 * 40,
    )
    return django.utils.timezone.make_aware(
        datetime.today() - timedelta(days=random_number_of_days),
    )


def _generate_log_entries(  # nosec: this is only used in a fixture
    fahrt_participants,
    superuser_frank,
):
    for participant in fahrt_participants:
        participant.log(
            superuser_frank if random.choice((True, False, False)) else None,
            "Signed up",
        )
        if participant.status != "registered":
            fahrt.models.LogEntry.objects.create(
                participant=participant,
                user=superuser_frank,
                text=participant.status,
            )
        if participant.payment_deadline:
            participant.log(
                superuser_frank,
                f"Set payment deadline to {participant.payment_deadline}",
            )
        if participant.non_liability:
            fahrt.models.LogEntry.objects.create(
                participant=participant,
                user=superuser_frank,
                text="Set non-liability",
                time=participant.non_liability,
            )
        if participant.mailinglist:
            participant.log(superuser_frank, "Toggle Mailinglist")


def _generate_superuser_frank():  # nosec: this is only used in a fixture
    return get_user_model().objects.create(
        username="frank",
        password="pbkdf2_sha256$216000$DHqZuXE7LQwJ$i8iIEB3qQN+NXMUTuRxKKFgYYC5XqlOYdSz/0om1FmE=",
        first_name="Frank",
        last_name="Elsinga",
        is_superuser=True,
        is_staff=True,
        is_active=True,
        email="elsinga@fs.tum.de",
        date_joined=django.utils.timezone.make_aware(datetime.today()),
    )


def _generate_fahrt_data():  # nosec: this is only used in a fixture
    return fahrt.models.Fahrt.objects.create(
        semester=settool_common.models.current_semester(),
        date=django.utils.timezone.make_aware(datetime.today() + timedelta(days=20)),
        open_registration=django.utils.timezone.make_aware(datetime.today() - timedelta(days=20)),
        close_registration=django.utils.timezone.make_aware(datetime.today() + timedelta(days=1)),
    )


def _generate_fahrt_participants(  # nosec: this is only used in a fixture
    common_subjects,
    fahrt_data,
):
    fahrt_participants = []
    for i in range(60):
        participant_has_car = random.choice((True, False, False))
        fahrt_participants.append(
            fahrt.models.Participant.objects.create(
                semester=fahrt_data.semester,
                gender=random.choice(fahrt.models.Participant.GENDER_CHOICES)[0],
                firstname=f"Firstname {i}",
                surname=f"Lastname {i}",
                birthday=generate_random_birthday(),
                email=f"{i}@test.com",
                phone=f"+49 89 {i:07d}",
                mobile=f"+49 176 {i:07d}",
                subject=random.choice(common_subjects),
                nutrition=random.choice(("normal", "vegeterian", "vegan")),
                allergies=random.choice(("gute Noten", "sport", "spargel"))
                if random.choice((True, False, False, False, False))
                else "",
                car=participant_has_car,
                car_places=random.randint(0, 6) if participant_has_car else None,
                non_liability=django.utils.timezone.make_aware(
                    datetime.today() - timedelta(random.randint(0, 4)),
                )
                if random.choice((True, True, False))
                else None,
                paid=django.utils.timezone.make_aware(
                    datetime.today() - timedelta(random.randint(0, 4)),
                )
                if random.choice((True, True, False))
                else None,
                payment_deadline=django.utils.timezone.make_aware(
                    datetime.today() + timedelta(random.randint(0, 10)),
                )
                if random.choice((True, True, True, False))
                else None,
                status=random.choice(
                    (
                        "registered",
                        "confirmed",
                        "registered",
                        "confirmed",
                        "waitinglist",
                        "cancelled",
                    ),
                ),
                mailinglist=random.choice((False, False, False, True)),
                comment=lorem.sentence() if random.choice((False, False, False, True)) else "",
            ),
        )
    return fahrt_participants


def _generate_guildedtours_participants(  # nosec: this is only used in a fixture
    common_subjects,
    guildedtours_tours,
):
    guildedtours_participants = []
    for tour in guildedtours_tours:
        for i in range(random.randint(0, tour.capacity)):
            guildedtours_participants.append(
                guidedtours.models.Participant.objects.create(
                    tour=tour,
                    firstname=f"Firstname {i}",
                    surname=f"Lastname {i}",
                    email=f"{i}@test.com",
                    phone=f"+49 176 {i:07d}",
                    subject=random.choice(common_subjects),
                ),
            )
    return guildedtours_participants


def _generate_guildedtours_tours(common_semesters):  # nosec: this is only used in a fixture
    guildedtours_tours = []
    for i in range(20):
        guildedtours_tours.append(
            guidedtours.models.Tour.objects.create(
                semester=random.choice(common_semesters),
                name=f"Tour {i}",
                description=lorem.sentence(),
                date=django.utils.timezone.make_aware(
                    datetime.today() + timedelta(days=random.randint(2, 20)),
                ),
                capacity=random.randint(5, 20),
                open_registration=django.utils.timezone.make_aware(
                    datetime.today() - timedelta(days=random.randint(1, 20)),
                ),
                close_registration=django.utils.timezone.make_aware(
                    datetime.today() + timedelta(days=random.randint(0, 1)),
                ),
            ),
        )
    return guildedtours_tours


def _generate_companies(common_semesters):  # nosec: this is only used in a fixture
    bags_companies = []
    for i in range(300):
        bags_companies.append(
            bags.models.Company.objects.create(
                semester=random.choice(common_semesters),
                name=f"Company {i}",
                contact_gender=random.choice(("Herr", "Frau", "")),
                contact_firstname=f"Firstname {i}",
                contact_lastname=f"Lastname {i}",
                email=f"{i}@test.com",
                email_sent=random.choice((True, False)),
                email_sent_success=random.choice((True, False)),
                promise=random.choice((True, False, None)),
                giveaways=lorem.sentence()[:50] if random.randint(0, 5) == 0 else "",
                giveaways_last_year=lorem.sentence()[:50] if random.randint(0, 5) == 0 else "",
                arrival_time=lorem.sentence()[:10] if random.randint(0, 5) < 3 else "",
                last_year=random.choice((True, False)),
                arrived=random.choice((True, False)),
                contact_again=random.choice((True, False)),
                comment=lorem.sentence()[:50] if random.randint(0, 5) == 0 else "",
            ),
        )
    return bags_companies


def _generate_tasks(events, tutors_list, questions):  # nosec: this is only used in a fixture
    tasks = []
    for event in events:
        number1 = random.randint(0, len(tutors_list))
        number2 = random.randint(0, len(tutors_list))
        filtered_questions = [
            question for question in questions if question.semester == event.semester
        ]
        event_subjects = list(event.subjects.all())
        for i in range(0, random.randint(0, 4)):
            task = tutors.models.Task.objects.create(
                semester=event.semester,
                name=f"Task {i}",
                description=lorem.paragraph(),
                begin=django.utils.timezone.make_aware(
                    datetime.today().replace(month=2).replace(day=1),
                ),
                end=django.utils.timezone.make_aware(
                    datetime.today().replace(month=11).replace(day=1),
                ),
                meeting_point=lorem.sentence()[: random.randint(0, 49)],
                event=event,
                min_tutors=min(number1, number2),
                max_tutors=max(number1, number2),
            )
            task.requirements.set(
                random.sample(filtered_questions, random.randint(0, len(filtered_questions))),
            )
            task.allowed_subjects.set(
                random.sample(event_subjects, random.randint(0, len(event_subjects))),
            )
            task.tutors.set(
                random.sample(
                    tutors_list,
                    random.randint(min(number1, number2), max(number1, number2)),
                ),
            )
            task.save()
            tasks.append(task)
    return tasks


def _generate_events(semesters, subjects):  # nosec: this is only used in a fixture
    events = []
    for i in range(10):
        event = tutors.models.Event.objects.create(
            semester=random.choice(semesters),
            name=f"Event {i}",
            description=lorem.paragraph(),
            begin=django.utils.timezone.make_aware(
                datetime.today().replace(month=1).replace(day=1),
            ),
            end=django.utils.timezone.make_aware(datetime.today().replace(month=1).replace(day=1)),
            meeting_point=lorem.sentence(),
        )
        filtered_subjects = random.sample(subjects, random.randint(0, len(subjects)))
        event.subjects.set(filtered_subjects)
        event.save()
        events.append(event)

    return events


def _generate_answers(questions, tutors_tutors):  # nosec: this is only used in a fixture
    answers = []
    for tutor in tutors_tutors:
        for question in questions:
            if random.randint(0, 5) == 0:
                answers.append(
                    tutors.models.Answer.objects.create(
                        tutor=tutor,
                        question=question,
                    ),
                )
            else:
                answers.append(
                    tutors.models.Answer.objects.create(
                        tutor=tutor,
                        question=question,
                        answer=random.choice(tutors.models.Answer.ANSWERS)[0],
                    ),
                )
    return answers


def _generate_questions(semesters):  # nosec: this is only used in a fixture
    questions = []
    for _ in range(5):
        questions.append(
            tutors.models.Question.objects.create(
                semester=random.choice(semesters),
                question=lorem.sentence(),
            ),
        )
    return questions


def _generate_common_mails(  # nosec: this is only used in a fixture
    semesters: List[settool_common.models.Semester],
) -> None:
    for author in settool_common.models.Mail.FROM_CHOICES:
        for _ in range(10):
            settool_common.models.Mail.objects.create(
                semester=random.choice(semesters),
                sender=author[0],
                subject=f"Common {lorem.sentence()}"[:100],
                text=lorem.text(),
            )


def _generate_bags_mails(  # nosec: this is only used in a fixture
    semesters: List[settool_common.models.Semester],
) -> None:
    for _ in range(10):
        bags.models.Mail.objects.create(
            semester=random.choice(semesters),
            subject=f"bags {lorem.sentence()}"[:100],
            text=lorem.text(),
            comment=lorem.sentence(),
        )


def _generate_guildedtours_mails(  # nosec: this is only used in a fixture
    semesters: List[settool_common.models.Semester],
) -> None:
    for _ in range(10):
        guidedtours.models.Mail.objects.create(
            semester=random.choice(semesters),
            subject=f"guidedtours {lorem.sentence()}"[:100],
            text=lorem.text(),
            comment=lorem.sentence(),
        )


def _generate_fahrt_mails(  # nosec: this is only used in a fixture
    semesters: List[settool_common.models.Semester],
) -> None:
    for _ in range(10):
        fahrt.models.Mail.objects.create(
            semester=random.choice(semesters),
            subject=f"fahrt {lorem.sentence()}"[:100],
            text=lorem.text(),
            comment=lorem.sentence(),
        )


def _generate_subjects():  # nosec: this is only used in a fixture
    subjects = []
    for subject_choice in settool_common.models.Subject.SUBJECT_CHOICES:
        for degree in settool_common.models.Subject.DEGREE_CHOICES:
            subjects.append(
                settool_common.models.Subject.objects.create(
                    subject=subject_choice[0],
                    degree=degree[0],
                ),
            )
    return subjects


def _generate_tutors(semesters, subjects):  # nosec: this is only used in a fixture
    tutors_ret = []
    for i in range(100):
        tutor = tutors.models.Tutor(
            semester=random.choice(semesters),
            first_name=f"Firstname_{i}",
            last_name=f"Lastname_{i}",
            email=f"{i}@test.com",
            subject=random.choice(subjects),
            tshirt_size=random.choice(tutors.models.Tutor.TSHIRT_SIZES)[0],
            tshirt_girls_cut=random.randint(0, 1) == 1,
            status=random.choice(
                (tutors.models.Tutor.STATUS_ACCEPTED, tutors.models.Tutor.STATUS_DECLINED),
            ),
            matriculation_number=f"{i:07d}",
            birthday=generate_random_birthday(),
        )
        tutors_ret.append(tutor)
        tutor.save()
    return tutors_ret
