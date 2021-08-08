import random
from datetime import timedelta
from subprocess import run  # nosec: used for flushing the db
from typing import Dict, List

import django.utils.timezone
import lorem
from django.contrib.auth import get_user_model
from django.utils.datetime_safe import datetime

import bags.models
import fahrt.models
import guidedtours.models
import kalendar.models
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


def showroom_fixture_state_no_confirmation():  # nosec: this is only used in a fixture
    run(["python3", "manage.py", "flush", "--noinput"], check=True)

    # user
    superuser_frank = _generate_superuser_frank()

    # app settool-common
    common_semesters = generate_semesters()
    common_subjects = _generate_subjects()

    # app bags
    _generate_mails(bags.models.BagMail, "bags")
    bags_companies = _generate_companies(common_semesters)
    _generate_giveaways(common_semesters, bags_companies)
    _generate_bags_settings(common_semesters)

    # app fahrt
    _generate_mails(fahrt.models.FahrtMail, "fahrt")
    fahrt_data = _generate_fahrt_data()
    fahrt_participants = _generate_fahrt_participants(common_subjects, fahrt_data)
    _generate_log_entries(fahrt_participants, superuser_frank)
    _generate_transportation(fahrt_participants)
    _generate_transportation_comment()

    # app guidedtours:
    _generate_mails(guidedtours.models.TourMail, "guidedtours")
    guidedtours_tours = _generate_guidedtours_tours(common_semesters)
    _generate_guidedtours_participants(common_subjects, guidedtours_tours)

    # app tutors
    _generate_mails(tutors.models.TutorMail, "tutor")
    tutors_list = _generate_tutors(common_semesters, common_subjects)
    tutors_questions = _generate_questions(common_semesters)
    _generate_answers(tutors_questions, tutors_list)
    tutors_events = _generate_events(common_semesters, common_subjects)
    _generate_tasks_tutorasignemt(tutors_events, tutors_list, tutors_questions)
    _generate_tutor_settings(common_semesters)
    # TODO tutors_mailtutortask
    # TODO tutors_subjecttutorcountassignment

    # app kalendar
    _generate_kalendar_locations()
    _generate_kalendar_date_groups()
    _generate_kalendar_dates()
    _generate_kalendar_subscriptions()


def _generate_kalendar_subscriptions():  # nosec: this is only used in a fixture
    actual_tutors = list(tutors.models.Tutor.objects.filter(status=tutors.models.Tutor.STATUS_ACCEPTED).all())
    collaborators = list(tutors.models.Tutor.objects.filter(status=tutors.models.Tutor.STATUS_EMPLOYEE).all())
    dates = list(kalendar.models.Date.objects.all())
    date_groups = list(kalendar.models.DateGroup.objects.all())
    for tutor in actual_tutors:
        if random.choice((True, True, True, False)):
            dates_for_tutor = random.randint(1, len(dates) // len(actual_tutors) + 1)
            selected_dates = random.sample(dates, dates_for_tutor)
            for date in selected_dates:
                kalendar.models.DateSubscriber.objects.create(date=date, tutor=tutor)
    for collaborator in collaborators:
        # 90% get a normal amount, 5% get nothing, 5% get all
        if random.randint(1, 100) > 10:
            date_groups_for_collaborator = random.randint(1, len(dates) // len(collaborators) + 1)
            selected_date_groups = random.sample(date_groups, date_groups_for_collaborator)
            for date_group in selected_date_groups:
                kalendar.models.DateGroupSubscriber.objects.create(date=date_group, tutor=collaborator)
        elif random.choice((True, False)):
            for date_group in date_groups:
                kalendar.models.DateGroupSubscriber.objects.create(date=date_group, tutor=collaborator)


def _generate_kalendar_locations():  # nosec: this is only used in a fixture
    locations = [
        "Fachschaftsbüro",
        "Serverraum",
        "LRZ",
        "Chemie-gebäude",
        "Interrims-Höhrsaal",
        "MI-Magistrale",
        "MI-Vorplazt",
        "Grillareal",
        "Galileo",
        "MW2001",
        "MW0001",
    ]
    for shortname in locations:
        address = random.choice(
            (
                f"Boltzmannstr. {random.randint(1, 30)}, 85748 Garching",
                random.choice(("Arcisstraße 17, 80333 München", "")),
            ),
        )
        kalendar.models.Location.objects.create(
            shortname=shortname,
            shortname_de=shortname,
            shortname_en=shortname,
            address=address,
            address_de=address,
            address_en=address,
            room=random.choice(("Magistrale", "FS-Büro", "MW0001", "MW2001", "007", "")),
            comment=lorem.sentence()[:200] if random.choice((True, False, False, False)) else "",
        )


def _generate_kalendar_date_groups():  # nosec: this is only used in a fixture
    locations: List[kalendar.models.Location] = list(kalendar.models.Location.objects.all())
    date_groups: List[kalendar.models.DateGroup] = list(kalendar.models.DateGroup.objects.all())
    for date_group in date_groups:
        if random.choice((True, True, True, False)):
            date_group.location = random.choice(locations)
        if random.choice((True, False, False, False)):
            date_group.comment = lorem.sentence()[:200]
        date_group.save()


def _generate_kalendar_dates():  # nosec: this is only used in a fixture
    date_groups: List[kalendar.models.DateGroup] = list(kalendar.models.DateGroup.objects.all())
    for date_group in date_groups:
        if random.choice((True, True, False)):
            for _ in range(random.choice((1, 1, 2, 2, 4, 4, 7, 7))):
                kalendar.models.Date.objects.create(
                    group=date_group,
                    date=django.utils.timezone.make_aware(
                        datetime.today()
                        + timedelta(days=random.randint(1, 60))
                        + timedelta(
                            hours=random.randint(0, 24),
                            minutes=random.randint(0, 60),
                        )
                        - timedelta(days=random.randint(1, 30)),
                    ),
                    probable_length=random.choice((60, 60, 60, 120, 240, 0, 1, 20)),
                )


def _generate_tutor_settings(common_semesters):  # nosec: this is only used in a fixture
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


def _generate_bags_settings(common_semesters):  # nosec: this is only used in a fixture
    for semester in common_semesters:
        if random.choice((True, True, False)):
            bags.models.BagSettings.objects.create(
                semester=semester,
                bag_count=random.randint(1000, 1500),
            )


def generate_random_birthday():  # nosec: this is only used in a fixture
    """
    :return: valid birthday that is 10..40 years in the past
    """
    random_number_of_days = random.randint(356 * 10, 365 * 40)
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


def _generate_transportation_comment():  # nosec: this is only used in a fixture
    transports = fahrt.models.Transportation.objects.all()
    for trans in transports:
        for _ in range(random.choice((0, 0, 1, 3))):
            if trans.participant_set.exists():
                fahrt.models.TransportationComment.objects.create(
                    sender=random.choice(list(trans.participant_set.all())),
                    commented_on=trans,
                    comment_content=lorem.sentence()[:200],
                )


def _generate_transportation(fahrt_participants):  # nosec: this is only used in a fixture
    transportation: List[fahrt.models.Transportation] = []
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
                deparure_place=random.choice([lorem.sentence(), "", ""]),
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


def _generate_fahrt_participants(  # nosec: this is only used in a fixture
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


def _generate_guidedtours_participants(  # nosec: this is only used in a fixture
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


def _generate_guidedtours_tours(common_semesters):  # nosec: this is only used in a fixture
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
                last_year=random.choice((True, False)),
                contact_again=random.choice((True, False)),
                comment=lorem.sentence()[:50] if random.randint(0, 5) == 0 else "",
            ),
        )
    return bags_companies


def _generate_giveaways(  # nosec: this is only used in a fixture
    semesters: List[settool_common.models.Semester],
    bags_companies: List[bags.models.Company],
) -> None:
    giveaway_groups: Dict[int, List[bags.models.GiveawayGroup]] = {}
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


def _generate_tasks_tutorasignemt(  # nosec: this is only used in a fixture
    events,
    tutors_list,
    questions,
):
    tasks = []
    all_tutors = list(tutors.models.Tutor.objects.all())
    for event in events:
        tutors_current_semester = [tutor for tutor in tutors_list if tutor.semester == event.semester]
        number1 = random.randint(0, len(tutors_current_semester))
        number2 = random.randint(0, len(tutors_current_semester))
        filtered_questions = [question for question in questions if question.semester == event.semester]
        event_subjects = list(event.subjects.all())
        for i in range(0, random.randint(0, 4)):
            person_1, person_2 = random.sample(all_tutors, 2)
            person_1 = random.choice((None, person_1, person_1, person_2, event.meeting_chairperson))
            person_2 = random.choice((None, person_2, person_2, event.event_leader))
            task = tutors.models.Task.objects.create(
                semester=event.semester,
                name_en=f"Task {i}",
                name_de=f"Task {i}",
                description_en=lorem.paragraph(),
                description_de=lorem.paragraph(),
                begin=django.utils.timezone.make_aware(
                    datetime.today().replace(day=1, month=1),
                ),
                end=django.utils.timezone.make_aware(
                    datetime.today().replace(day=1, month=12),
                ),
                meeting_chairperson=person_1,
                task_leader=person_2,
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


def _generate_events(semesters, subjects):  # nosec: this is only used in a fixture
    all_tutors = list(tutors.models.Tutor.objects.all())
    events = []
    for i in range(random.randint(10, 20)):
        person_1, person_2 = random.sample(all_tutors, 2)
        person_1 = random.choice((None, person_1))
        person_2 = random.choice((None, person_2))
        event = tutors.models.Event.objects.create(
            semester=random.choice(semesters),
            name=f"Event {i}",
            name_en=f"Event {i}",
            name_de=f"Event {i}",
            description_en=lorem.paragraph(),
            description_de=lorem.paragraph(),
            meeting_chairperson=person_1,
            event_leader=person_2,
            begin=django.utils.timezone.make_aware(
                datetime.today().replace(day=1, month=1),
            ),
            end=django.utils.timezone.make_aware(datetime.today().replace(day=1, month=1)),
        )
        filtered_subjects = random.sample(subjects, random.randint(0, len(subjects)))
        event.subjects.set(filtered_subjects)
        event.save()
        events.append(event)

    return events


def _generate_answers(questions, tutors_list):  # nosec: this is only used in a fixture
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


def _generate_questions(semesters):  # nosec: this is only used in a fixture
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


def _generate_mails(cls, app_id):  # nosec: this is only used in a fixture
    for _ in range(random.randint(10, 20)):
        cls.objects.create(
            subject=f"{app_id} {lorem.sentence()}"[:100],
            text=lorem.text(),
            comment=lorem.sentence(),
        )


def generate_common_mails():
    _generate_mails(bags.models.BagMail, "bags")
    _generate_mails(fahrt.models.FahrtMail, "fahrt")
    _generate_mails(tutors.models.TutorMail, "tutor")
    _generate_mails(guidedtours.models.TourMail, "guidedtours")


def _generate_subjects():  # nosec: this is only used in a fixture
    subjects = []

    course_bundle_mathe = settool_common.models.CourseBundle.objects.create(
        name="Mathe",
        name_de="Mathematics",
        name_en="Mathematik",
    )
    course_bundle_physik = settool_common.models.CourseBundle.objects.create(
        name="Physik",
        name_de="Physics",
        name_en="Physik",
    )
    course_bundle_info = settool_common.models.CourseBundle.objects.create(
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

    sub_trans = [
        ("Mathe", "Mathematics", "Mathematik", course_bundle_mathe),
        ("Physik", "Physics", "Physik", course_bundle_physik),
        ("Info", "Informatics", "Informatik", course_bundle_info),
        ("Games", "Informatics: Games Engineering", "Informatik: Games Engineering", course_bundle_info),
        ("Winfo", "Information Systems", "Wirtschaftsinformatik", course_bundle_info),
        ("ASE", "Automotive Software Engineering", "Automotive Software Engineering", course_bundle_info),
        ("CSE", "Computational Science and Engineering", "Computational Science and Engineering", course_bundle_info),
        ("BMC", "Biomedical Computing", "Biomedical Computing", course_bundle_info),
        ("Robotics", "Robotics, Cognition, Intelligence", "Robotics, Cognition, Intelligence", course_bundle_info),
        ("Mathe OR", "Mathematics in Operatios Research", "Mathematics in Operatios Research", course_bundle_mathe),
        (
            "Mathe SE",
            "Mathematics in Science and Engineering",
            "Mathematics in Science and Engineering",
            course_bundle_mathe,
        ),
        (
            "Mathe Finance",
            "Mathematics in Finance and Acturial Science",
            "Mathematics in Finance and Acturial Science",
            course_bundle_mathe,
        ),
        ("Mathe Bio", "Mathematics in Bioscience", "Mathematics in Bioscience", course_bundle_mathe),
    ]

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
            status=random.choice(tutors.models.Tutor.STATUS_OPTIONS)[0],
            matriculation_number=f"{i:08d}",
            birthday=generate_random_birthday(),
        )
        tutors_ret.append(tutor)
        tutor.save()
    return tutors_ret
