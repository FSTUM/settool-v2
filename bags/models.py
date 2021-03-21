from typing import List, Tuple

from django.db import models
from django.utils.translation import ugettext_lazy as _

import settool_common.models as common_models
from settool_common.models import Semester


class BagMail(common_models.Mail):
    # ["{{template}}", "description"]
    general_placeholders = [
        ("{{firma}}", _("The company name")),
        ("{{anrede}}", _("The greeting 'Hallo Herr/Frau XYZ'")),
        ("{{formale_anrede}}", _("The formal greeting 'Sehr geehrte/r " "Herr/Frau XYZ'")),
    ]
    # ["{{template}}", "description", "contition"]
    conditional_placeholders: List[Tuple[str, str, str]] = []
    notes = ""

    required_perm = common_models.Mail.required_perm + ["bags.view_companies"]

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        self.sender = common_models.Mail.SET_BAGS
        super().save(*args, **kwargs)

    def send_mail_company(self, company):
        context = {
            "firma": company.name,
            "anrede": company.anrede,
            "formale_anrede": company.formale_anrede,
        }
        return self.send_mail(context, company.email)

    def get_mail_company(self):
        context = {
            "firma": "<Firma>",
            "anrede": "<Hallo Herr/Frau XYZ>",
            "formale_anrede": "<Sehr geehrte/r Herr/Frau XYZ>",
        }
        return self.get_mail(context)


class Company(models.Model):
    class Meta:
        unique_together = ("semester", "name")
        permissions = (
            (
                "view_companies",
                "Can view and edit the companies",
            ),
        )

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        _("Name"),
        max_length=200,
    )

    contact_gender = models.CharField(
        _("Contact person (Gender)"),
        max_length=200,
        choices=(("Herr", _("Herr")), ("Frau", _("Frau"))),
        blank=True,
    )

    contact_firstname = models.CharField(
        _("Contact person (First Name)"),
        max_length=200,
        blank=True,
    )

    contact_lastname = models.CharField(
        _("Contact person (Last Name)"),
        max_length=200,
        blank=True,
    )

    email = models.EmailField(
        _("Email address"),
    )

    email_sent = models.BooleanField(
        _("Email sent"),
    )

    email_sent_success = models.BooleanField(
        _("Email successfully sent"),
    )

    promise = models.BooleanField(
        _("Promise"),
        null=True,
    )

    comment = models.CharField(
        _("Comment"),
        max_length=200,
        blank=True,
    )

    last_year = models.BooleanField(
        _("Participated last year"),
    )

    contact_again = models.BooleanField(
        _("Contact again"),
        null=True,
    )

    def __str__(self):
        return str(self.name)

    @property
    def full_contact(self):
        return f"{self.contact_gender} {self.contact_firstname} {self.contact_lastname}"

    @property
    def anrede(self):
        if self.contact_gender and self.contact_lastname:
            return f"Hallo {self.contact_gender} {self.contact_lastname}"
        return "Sehr geehrte Damen und Herren"

    @property
    def formale_anrede(self):
        if self.contact_gender and self.contact_lastname:
            if self.contact_gender == "Herr":
                return f"Sehr geehrter Herr {self.contact_lastname}"
            if self.contact_gender == "Frau":
                return f"Sehr geehrte Frau {self.contact_lastname}"
            return "Sehr geehrte Damen und Herren"
        return "Sehr geehrte Damen und Herren"

    @property
    def contact_name(self):
        return f"{self.contact_firstname} {self.contact_lastname}"


class GiveawayGroup(models.Model):
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        _("Giveaway-groups' name"),
        max_length=200,
    )

    def __str__(self):
        return self.name


class Giveaway(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
    )
    group = models.ForeignKey(
        GiveawayGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField(
        _("Giveaway-title"),
        max_length=200,
    )
    every_x_bags = models.FloatField(
        verbose_name=_("Insert every x bags"),
        default=1.0,
    )
    per_bag_count = models.PositiveSmallIntegerField(
        verbose_name=_("Capacity per Bag"),
        default=1,
    )
    arrival_time = models.CharField(
        _("Arrival time"),
        max_length=200,
        blank=True,
    )

    arrived = models.BooleanField(
        _("Arrived"),
        default=False,
    )

    @property
    def custom_per_bag_message(self):
        if self.per_bag_count == 0 or self.every_x_bags == 0.0:
            return _("Wont be included in any bags")
        if self.per_bag_count == 1:
            return _("{per_bag_count} per bag").format(per_bag_count=self.per_bag_count)
        return _("{per_bag_count} every {every_x_bags} bags").format(
            per_bag_count=self.per_bag_count,
            every_x_bags=self.every_x_bags,
        )

    def __str__(self):
        if self.group:
            return f"{self.name} ({self.group}; {self.custom_per_bag_message})"
        return f"{self.name} ({self.custom_per_bag_message})"
