import json
from csv import DictReader
from decimal import Decimal, InvalidOperation
from typing import Any

from django.utils.datetime_safe import date, datetime


# pylint: disable=too-many-arguments
class Entry:
    def __init__(self, datum, verwendungszweck, zahlungspflichtiger, iban, bic, betrag):
        self.datum: date = datum
        self.verwendungszweck: str = verwendungszweck
        self.zahlungspflichtiger: str = zahlungspflichtiger
        self.iban: str = iban
        self.bic: str = bic
        self.betrag: str = betrag

    def to_json(self):
        dump = self.__dict__.copy()
        dump["datum"] = self.datum.strftime("%d.%m.%y")
        return json.dumps(dump)

    @staticmethod
    def from_json(json_str):
        entity_dict = json.loads(json_str)
        return Entry(
            datum=Entry.parse_date(entity_dict["datum"]),
            verwendungszweck=entity_dict["verwendungszweck"],
            zahlungspflichtiger=entity_dict["zahlungspflichtiger"],
            iban=entity_dict["iban"],
            bic=entity_dict["bic"],
            betrag=entity_dict["betrag"],
        )

    def __repr__(self):
        return (
            f"Entry <"
            f"datum={self.datum}, "
            f'verwendungszweck="{self.verwendungszweck}", '
            f'zahlungspflichtiger="{self.zahlungspflichtiger}", '
            f"iban={self.iban}, "
            f"bic={self.bic}, "
            f"betrag={self.betrag}>"
        )

    @classmethod
    def parse_date(cls, s_date: str) -> Any:
        try:
            return datetime.strptime(s_date, "%d.%m.%y").date()
        except ValueError:
            return datetime.strptime(s_date, "%d.%m.%Y").date()


def parse_camt_csv(csvfile):
    results = []
    errors = []

    csv_contents = DictReader(csvfile, delimiter=";")
    for counter, row in enumerate(csv_contents):
        buchungstext = row["Buchungstext"]
        if buchungstext in ["GUTSCHR. UEBERWEISUNG", "ECHTZEIT-GUTSCHRIFT"]:
            try:
                datum = Entry.parse_date(row["Buchungstag"])
            except ValueError:
                errors.append(f"Zeile {counter}: Ungültiges Datum: {row['Buchungstag']}")
                continue

            betrag = row["Betrag"].replace(",", ".")
            try:
                Decimal(betrag)
            except InvalidOperation:
                errors.append(
                    f"Zeile {counter}: Ungültiger Betrag: {betrag}",
                )
                continue

            waehrung = row["Waehrung"]
            if waehrung != "EUR":
                errors.append(f"Zeile {counter}: Eintrag in anderer Währung als Euro")
                continue

            entry = Entry(
                datum,
                row["Verwendungszweck"],
                row["Beguenstigter/Zahlungspflichtiger"],
                row["Kontonummer/IBAN"],
                row["BIC (SWIFT-Code)"],
                betrag,
            )
            results.append(entry.to_json())

        elif buchungstext in [
            "ENTGELTABSCHLUSS",
            "ONLINE-UEBERWEISUNG",
            "RECHNUNG",
            "FOLGELASTSCHRIFT",
            "BARGELDAUSZAHLUNG KASSE",
        ]:
            pass
        else:
            errors.append(f"Transaktion in Zeile {counter} mit Typ {buchungstext} nicht erkannt")
    return results, errors
