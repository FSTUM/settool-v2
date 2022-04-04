from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.aggregates import Sum
from django.utils.translation import gettext_lazy as _

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
    conditional_placeholders: list[tuple[str, str, str]] = []
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


class BagSettings(models.Model):
    semester = models.OneToOneField(Semester, on_delete=models.CASCADE)
    bag_count = models.PositiveSmallIntegerField(verbose_name=_("Total amount of Bags"), default=0)

    def __str__(self) -> str:
        return f"Bag-Settings for {self.semester}"


class Company(models.Model):
    class Meta:
        unique_together = ("semester", "name")
        permissions = (("view_companies", "Can view and edit the companies"),)

    semester = models.ForeignKey(Semester,on_delete=models.CASCADE)

    name = models.CharField(_("Name"), max_length=200)

    contact_gender = models.CharField(
        _("Contact person (Gender)"),
        max_length=200,
        choices=(("Herr", _("Herr")), ("Frau", _("Frau"))),
        blank=True,
    )
    contact_firstname = models.CharField(_("Contact person (First Name)"), max_length=200, blank=True)
    contact_lastname = models.CharField(_("Contact person (Last Name)"), max_length=200, blank=True)

    email = models.EmailField(_("Email address"))
    email_sent = models.BooleanField(_("Email sent"))
    email_sent_success = models.BooleanField(_("Email successfully sent"))

    promise = models.BooleanField(_("Promise"), null=True)
    last_year = models.BooleanField(_("Participated last year"))
    contact_again = models.BooleanField(_("Contact again"), null=True)

    comment = models.CharField(_("Comment"), max_length=200, blank=True)

    def __str__(self) -> str:
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
    class Meta:
        unique_together = (("semester", "name"),)

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
    )

    name = models.CharField(
        _("Giveaway-groups' name"),
        max_length=200,
    )

    def __str__(self) -> str:
        return self.name

    @property
    def total_items(self) -> int:
        return self.giveaway_set.aggregate(Sum("item_count"))["item_count__sum"] or 0

    @property
    def custom_per_group_message(self):
        total_items = self.total_items
        if total_items == 0:
            return _("Does not exist")
        try:
            total_bags = self.semester.bagsettings.bag_count
        except ObjectDoesNotExist:
            return _("Total amount of Bags is not specified")
        if total_bags == 0:
            return _("Total amount of Bags is zero")
        if total_items == total_bags:
            return _("Every bag")
        if total_items < total_bags:
            return _("Every {every_x_bags}th bag").format(
                every_x_bags=round(total_bags / total_items, 1),
            )
        return _("{per_bag_count} every bag").format(per_bag_count=round(total_items / total_bags, 1))


class Giveaway(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    group = models.ForeignKey(
        GiveawayGroup,
        verbose_name=_("Giveaway-title/group/tag"),
        on_delete=models.SET_NULL,
        null=True,
    )

    item_count = models.PositiveSmallIntegerField(verbose_name=_("Item Count"), default=0)

    arrival_time = models.CharField(_("Arrival time"), max_length=200, blank=True)
    arrived = models.BooleanField(_("Arrived"), default=False)

    comment = models.CharField(_("Giveaway-description/comment"), blank=True, max_length=200)

    @property
    def custom_per_bag_message(self):
        if self.item_count == 0:
            return _("Does not exist")
        try:
            total_bags = self.company.semester.bagsettings.bag_count
        except ObjectDoesNotExist:
            return _("Total amount of Bags is not specified")
        if total_bags == 0:
            return _("Total amount of Bags is zero")
        if self.item_count == total_bags:
            return _("Every bag")
        if self.item_count < total_bags:
            return _("Every {every_x_bags}th bag").format(
                every_x_bags=round(total_bags / self.item_count, 1),
            )
        return _("{per_bag_count} every bag").format(per_bag_count=round(self.item_count / total_bags, 1))

    def __str__(self) -> str:
        if self.comment:
            return f"{self.group or '-'} ({self.comment or '-'}; {self.custom_per_bag_message})"
        return f"{self.group or '-'} ({self.custom_per_bag_message})"
