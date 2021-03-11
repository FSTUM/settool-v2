import json
from csv import DictReader
from decimal import InvalidOperation

from django.utils.datetime_safe import datetime


# pylint: disable=too-many-arguments
class Entry:
    def __init__(
        self,
        datum=None,
        verwendungszweck=None,
        zahlungspflichtiger=None,
        iban=None,
        bic=None,
        betrag=None,
    ):
        self.datum = datum
        self.verwendungszweck = verwendungszweck
        self.zahlungspflichtiger = zahlungspflichtiger
        self.iban = iban
        self.bic = bic
        self.betrag = betrag

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    @staticmethod
    def from_json(json_str):
        entity_dict = json.loads(json_str)
        return Entry(
            datum=entity_dict["datum"],
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


def parse_camt_csv(csvfile):
    results = []
    errors = []

    # read CSV file
    csvcontents = DictReader(csvfile, delimiter=";")
    for counter, row in enumerate(csvcontents):

        buchungstext = row["Buchungstext"]
        if buchungstext in ["GUTSCHR. UEBERWEISUNG", "ECHTZEIT-GUTSCHRIFT"]:
            entry = Entry()

            try:
                entry.datum = datetime.strptime(row["Buchungstag"], "%d.%m.%y").date()
            except ValueError:
                try:
                    entry.datum = datetime.strptime(row["Buchungstag"], "%d.%m.%Y").date()
                except ValueError:
                    errors.append(f"Zeile {counter}: Ungültiges Datum: {row['Buchungstag']}")
                    continue

            entry.verwendungszweck = row["Verwendungszweck"]
            entry.zahlungspflichtiger = row["Beguenstigter/Zahlungspflichtiger"]
            entry.iban = row["Kontonummer/IBAN"]
            entry.bic = row["BIC (SWIFT-Code)"]

            betrag = row["Betrag"]
            try:
                entry.betrag = betrag.replace(",", ".")
            except InvalidOperation:
                errors.append(
                    f"Zeile {counter}: Ungültiger Betrag: {betrag}",
                )
                continue

            waehrung = row["Waehrung"]
            if waehrung != "EUR":
                errors.append(
                    f"Zeile {counter}: Eintrag in anderer Währung als Euro",
                )
                continue

            results.append(entry.to_json())
        # TODO Check if this is ok
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
