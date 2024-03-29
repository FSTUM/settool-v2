import random
from datetime import timedelta
from pathlib import Path
from subprocess import run  # nosec: used for flushing the db

import django.utils.timezone
import lorem
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.datetime_safe import datetime

import bags.models
import fahrt.models
import guidedtours.models
import settool_common.models
import tutors.models
from settool_common.fixtures.test_fixture import generate_semesters


def showroom_fixture_state():
    confirmation = input(
        "Do you really want to load the showroom fixture? (This will flush the database) [y/n]",
    )
    if confirmation.lower() != "y":
        return
    showroom_fixture_state_no_confirmation()


def showroom_fixture_state_no_confirmation():
    run(["python3", Path(__file__).parent.parent.parent / "manage.py", "flush", "--noinput"], check=True)

    # user
    _generate_superusers()

    # mails
    generate_all_mails()

    # app settool-common
    common_semesters = generate_semesters()
    common_subjects = _generate_subjects()

    # app bags
    bags_companies = _generate_companies(common_semesters)
    _generate_giveaways(common_semesters, bags_companies)
    _generate_bags_settings(common_semesters)

    # app fahrt
    fahrt_data = _generate_fahrt_data()
    fahrt_participants = _generate_fahrt_participants(common_subjects, fahrt_data)
    _generate_log_entries(fahrt_participants)
    _generate_transportation(fahrt_participants)
    _generate_transportation_comment()

    # app guidedtours:
    guidedtours_tours = _generate_guidedtours_tours(common_semesters)
    _generate_guidedtours_participants(common_subjects, guidedtours_tours)

    # app tutors
    tutors_list = _generate_tutors(common_semesters, common_subjects)
    tutors_questions = _generate_questions(common_semesters)
    _generate_answers(tutors_questions, tutors_list)
    tutors_events = _generate_events(common_semesters, common_subjects)
    _generate_tasks_tutorasignemt(tutors_events, tutors_list, tutors_questions)
    _generate_tutor_settings(common_semesters)
    # TODO tutors_mailtutortask
    # TODO tutors_subjecttutorcountassignment


def _generate_tutor_settings(common_semesters):
    all_mail_by_set_tutor = tutors.models.TutorMail.objects.all()
    for semester in common_semesters:
        if random.choice((True, True, False)):
            tutors.models.Settings.objects.create(
                semester=semester,
                open_registration=django.utils.timezone.make_aware(datetime.today() - timedelta(days=20)),
                close_registration=django.utils.timezone.make_aware(datetime.today() + timedelta(days=20)),
                mail_registration=all_mail_by_set_tutor[0],
                mail_confirmed_place=all_mail_by_set_tutor[1],
                mail_waiting_list=all_mail_by_set_tutor[2],
                mail_declined_place=all_mail_by_set_tutor[3],
                mail_task=all_mail_by_set_tutor[4],
            )


def _generate_bags_settings(common_semesters):
    for semester in common_semesters:
        if random.choice((True, True, False)):
            bags.models.BagSettings.objects.create(
                semester=semester,
                bag_count=random.randint(1000, 1500),
            )


def generate_random_birthday():
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


def _generate_log_entries(fahrt_participants):
    users = list(get_user_model().objects.all())
    for participant in fahrt_participants:
        participant.log(
            random.choice(users) if random.choice((True, False, False)) else None,
            "Signed up",
        )
        if participant.status != "registered":
            fahrt.models.LogEntry.objects.create(
                participant=participant,
                user=random.choice(users),
                text=participant.status,
            )
        if participant.payment_deadline:
            participant.log(random.choice(users), f"Set payment deadline to {participant.payment_deadline}")
        if participant.non_liability:
            fahrt.models.LogEntry.objects.create(
                participant=participant,
                user=random.choice(users),
                text="Set non-liability",
                time=participant.non_liability,
            )
        if participant.mailinglist:
            participant.log(random.choice(users), "Toggle Mailinglist")


def _generate_superusers() -> None:
    users = [
        ("frank", "130120", "Frank", "Elsinga", "elsinga@example.com"),
        ("password", "username", "Nelson 'Big Head'", "Bighetti", "bighetti@example.com"),
    ]
    for username, password, first_name, last_name, email in users:
        get_user_model().objects.create(
            username=username,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
            is_superuser=True,
            is_staff=True,
            is_active=True,
            email=email,
            date_joined=django.utils.timezone.make_aware(datetime.today()),
        )


def _generate_fahrt_data():
    return fahrt.models.Fahrt.objects.create(
        semester=settool_common.models.current_semester(),
        date=django.utils.timezone.make_aware(datetime.today() + timedelta(days=20)),
        open_registration=django.utils.timezone.make_aware(datetime.today() - timedelta(days=20)),
        close_registration=django.utils.timezone.make_aware(datetime.today() + timedelta(days=1)),
    )


def _generate_transportation_comment():
    transports = fahrt.models.Transportation.objects.all()
    for trans in transports:
        for _ in range(random.choice((0, 0, 1, 3))):
            if trans.participant_set.exists():
                fahrt.models.TransportationComment.objects.create(
                    sender=random.choice(list(trans.participant_set.all())),
                    commented_on=trans,
                    comment_content=lorem.sentence()[:200],
                )


def _generate_transportation(fahrt_participants):
    transportation: list[fahrt.models.Transportation] = []
    participant: fahrt.models.Participant
    counter = 0
    for participant in fahrt_participants:
        if not participant.transportation and participant.status == "confirmed":
            counter += 1
            if counter > 5:
                break
            transport_type = random.choice((fahrt.models.Transportation.CAR, fahrt.models.Transportation.TRAIN))
            if transport_type == fahrt.models.Transportation.TRAIN:
                places_count = 5
            else:
                places_count = random.choice((1, 3, 4, 4, 5, 5, 5, 7))
            trans: fahrt.models.Transportation = fahrt.models.Transportation.objects.create(
                transport_type=transport_type,
                creator=participant,
                fahrt=participant.semester.fahrt,
                deparure_time=random.choice(
                    [participant.semester.fahrt.date + timedelta(hours=random.randint(-5, 5)), None],
                ),
                return_departure_time=random.choice(
                    [participant.semester.fahrt.date + timedelta(hours=random.randint(-5, 5)), None],
                ),
                departure_place=random.choice([lorem.sentence(), "", ""]),
                places=places_count,
            )
            participant.transportation = trans
            participant.save()
            if trans.places > trans.participant_set.count():
                transportation.append(trans)
    for participant in fahrt_participants:
        p_is_no_creator = not any(trans.creator == participant for trans in transportation)
        if p_is_no_creator and len(transportation) > 3 and participant.status == "confirmed":
            trans = random.choice(transportation)
            participant.transportation = trans
            participant.save()
            if trans.places == trans.participant_set.count():
                transportation.remove(trans)


def _generate_fahrt_participants(
    common_subjects,
    fahrt_data,
):
    fahrt_participants = []
    for i in range(60):
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
                publish_contact_to_other_paricipants=random.choice((True, True, False)),
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


def _generate_guidedtours_participants(
    common_subjects,
    guidedtours_tours,
):
    guidedtours_participants = []
    for tour in guidedtours_tours:
        for i in range(random.randint(int(tour.capacity * 0.7), int(tour.capacity * 1.5))):
            guidedtours_participants.append(
                guidedtours.models.Participant.objects.create(
                    tour=tour,
                    firstname=f"Firstname {i}",
                    surname=f"Lastname {i}",
                    email=f"{i}@test.com",
                    phone=f"+49 176 {i:07d}",
                    subject=random.choice(common_subjects),
                ),
            )
    return guidedtours_participants


def _generate_guidedtours_tours(common_semesters):
    guidedtours_tours = []
    for i in range(50):
        guidedtours_tours.append(
            guidedtours.models.Tour.objects.create(
                semester=random.choice(common_semesters),
                name=f"Tour {i}",
                description=lorem.sentence(),
                date=django.utils.timezone.make_aware(
                    datetime.today() + timedelta(days=random.randint(2, 20)),
                ),
                capacity=random.randint(15, 30),
                open_registration=django.utils.timezone.make_aware(
                    datetime.today() - timedelta(days=random.randint(1, 20)),
                ),
                close_registration=django.utils.timezone.make_aware(
                    datetime.today() + timedelta(days=random.randint(0, 1)),
                ),
            ),
        )
    return guidedtours_tours


def _generate_companies(common_semesters):
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
                last_year=random.choice((True, False)),
                contact_again=random.choice((True, False)),
                comment=lorem.sentence()[:50] if random.randint(0, 5) == 0 else "",
            ),
        )
    return bags_companies


def _generate_giveaways(
    semesters: list[settool_common.models.Semester],
    bags_companies: list[bags.models.Company],
) -> None:
    giveaway_groups: dict[int, list[bags.models.GiveawayGroup]] = {}
    for i in range(10):
        giveaway_group = bags.models.GiveawayGroup.objects.create(
            semester=random.choice(semesters),
            name=f"GiveawayGroup {i}",
        )
        if giveaway_group.semester.id not in giveaway_groups:
            giveaway_groups[giveaway_group.semester.id] = []
        giveaway_groups[giveaway_group.semester.id].append(giveaway_group)
    for _ in range(int(len(bags_companies) * 0.25)):
        company = random.choice(bags_companies)
        group = None
        if random.choice((True, True, False)) and company.semester.id in giveaway_groups:
            group = random.choice(giveaway_groups[company.semester.id])
        bags.models.Giveaway.objects.create(
            company=company,
            group=group,
            comment=lorem.sentence()[:50],
            item_count=round(random.randint(0, 2500), -1),
            arrival_time=random.choice(
                (
                    random.choice(
                        (
                            "never",
                            "yesterday",
                            "tomorrow",
                            "st.nimmerleinstag",
                            "wenn amazon bock hat",
                            "wenn dhl bock hat",
                            "wenn dpd bock hat",
                            "wenn die Poststelle bock hat",
                        ),
                    ),
                    lorem.sentence()[:10],
                    "",
                ),
            ),
            arrived=random.choice((True, False)),
        )


def _generate_tasks_tutorasignemt(
    events,
    tutors_list,
    questions,
):
    tasks = []
    for event in events:
        tutors_current_semester = [tutor for tutor in tutors_list if tutor.semester == event.semester]
        number1 = random.randint(0, len(tutors_current_semester))
        number2 = random.randint(0, len(tutors_current_semester))
        filtered_questions = [question for question in questions if question.semester == event.semester]
        event_subjects = list(event.subjects.all())
        for i in range(0, random.randint(0, 4)):
            task = tutors.models.Task.objects.create(
                semester=event.semester,
                name_en=f"Task {i}",
                name_de=f"Task {i}",
                description_en=lorem.paragraph(),
                description_de=lorem.paragraph(),
                begin=django.utils.timezone.make_aware(
                    datetime.today().replace(day=1, month=1)
                    + timedelta(days=random.randint(0, 30), minutes=random.randint(1, 1000)),
                ),
                end=django.utils.timezone.make_aware(
                    datetime.today().replace(day=1, month=12)
                    - timedelta(days=random.randint(0, 30), minutes=random.randint(1, 1000)),
                ),
                meeting_point_en=lorem.sentence()[: random.randint(0, 49)],
                meeting_point_de=lorem.sentence()[: random.randint(0, 49)],
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
            tutors_for_task = random.sample(
                tutors_current_semester,
                random.randint(min(number1, number2), max(number1, number2)),
            )
            for tutor in tutors_for_task:
                tutors.models.TutorAssignment.objects.create(
                    task=task,
                    tutor=tutor,
                )

            task.save()
            tasks.append(task)
    return tasks


def _generate_events(semesters, subjects):
    events = []
    for i in range(random.randint(10, 20)):
        event = tutors.models.Event.objects.create(
            semester=random.choice(semesters),
            name=f"Event {i}",
            name_en=f"Event {i}",
            name_de=f"Event {i}",
            description_en=lorem.paragraph(),
            description_de=lorem.paragraph(),
            begin=django.utils.timezone.make_aware(
                datetime.today().replace(day=1, month=1)
                + timedelta(days=random.randint(0, 30), minutes=random.randint(1, 1000)),
            ),
            end=django.utils.timezone.make_aware(
                datetime.today().replace(day=1, month=12)
                - timedelta(days=random.randint(0, 30), minutes=random.randint(1, 1000)),
            ),
            meeting_point_en=lorem.sentence(),
            meeting_point_de=lorem.sentence(),
        )
        filtered_subjects = random.sample(subjects, random.randint(0, len(subjects)))
        event.subjects.set(filtered_subjects)
        event.save()
        events.append(event)

    return events


def _generate_answers(questions, tutors_list):
    answers = []
    for tutor in tutors_list:
        questions_tutor_semester = [question for question in questions if question.semester == tutor.semester]
        for question in questions_tutor_semester:
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


def _generate_questions(semesters):
    questions = []
    for semester in semesters:
        for _ in range(random.choice((2, 3))):
            questions.append(
                tutors.models.Question.objects.create(
                    semester=semester,
                    question_en=lorem.sentence(),
                    question_de=lorem.sentence(),
                ),
            )
    return questions


def _generate_subjects():
    subjects = []

    cb_mathe = settool_common.models.CourseBundle.objects.create(name="Mathe", name_de="Maths", name_en="Mathematik")
    cb_physik = settool_common.models.CourseBundle.objects.create(name="Physik", name_de="Physics", name_en="Physik")
    cb_info = settool_common.models.CourseBundle.objects.create(
        name="Info",
        name_de="Informatics",
        name_en="Informatik",
    )
    settool_common.models.CourseBundle.objects.create(name="Data", name_de="Data Science", name_en="Data Science")
    settool_common.models.CourseBundle.objects.create(
        name="EEng",
        name_de="Elektrotechnik",
        name_en="Electrical Engeneering",
    )

    sub_trans = (
        [
            ("Physik", "Physics", "Physik", cb_physik),
        ]
        + [
            ("Info", "Informatics", "Informatik", cb_info),
            ("Games", "Informatics: Games Engineering", "Informatik: Games Engineering", cb_info),
            ("Winfo", "Information Systems", "Wirtschaftsinformatik", cb_info),
            ("ASE", "Automotive Software Engineering", "Automotive Software Engineering", cb_info),
            ("CSE", "Computational Science and Engineering", "Computational Science and Engineering", cb_info),
            ("BMC", "Biomedical Computing", "Biomedical Computing", cb_info),
            ("Robotics", "Robotics, Cognition, Intelligence", "Robotics, Cognition, Intelligence", cb_info),
        ]
        + [
            ("Mathe", "Mathematics", "Mathematik", cb_mathe),
            ("Mathe OR", "Mathematics in Operations Research", "Mathematics in Operations Research", cb_mathe),
            ("Mathe Bio", "Mathematics in Bioscience", "Mathematics in Bioscience", cb_mathe),
            (
                "Mathe SE",
                "Mathematics in Science and Engineering",
                "Mathematics in Science and Engineering",
                cb_mathe,
            ),
            (
                "Mathe Finance",
                "Mathematics in Finance and Acturial Science",
                "Mathematics in Finance and Acturial Science",
                cb_mathe,
            ),
        ]
    )

    for subject_choice, subject_choice_en, subject_choice_de, course_bundle in sub_trans:
        for degree in [settool_common.models.Subject.MASTER, settool_common.models.Subject.BACHELOR]:
            subjects.append(
                settool_common.models.Subject.objects.create(
                    subject=subject_choice,
                    subject_de=subject_choice_de,
                    subject_en=subject_choice_en,
                    course_bundle=course_bundle,
                    degree=degree,
                ),
            )
    return subjects


def _generate_tutors(semesters, subjects):
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
            status=random.choice(tutors.models.Tutor.STATUS_OPTIONS)[0],
            matriculation_number=f"{i:08d}",
            birthday=generate_random_birthday(),
        )
        tutors_ret.append(tutor)
        tutor.save()
    return tutors_ret


def _generate_mails(cls, app_id):
    for _ in range(random.randint(10, 20)):
        cls.objects.create(
            subject=f"{app_id} {lorem.sentence()}"[:100],
            text=lorem.text(),
            comment=lorem.sentence(),
        )


def generate_all_mails():
    _generate_mails(bags.models.BagMail, "bags")
    _generate_mails(fahrt.models.FahrtMail, "fahrt")
    _generate_mails(tutors.models.TutorMail, "tutor")
    _generate_mails(guidedtours.models.TourMail, "guidedtours")
