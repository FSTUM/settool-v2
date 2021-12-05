from django.core.management.commands import makemessages


class Command(makemessages.Command):
    def build_potfiles(self):
        potfiles = super().build_potfiles()

        for potfile in sorted(set(potfiles)):
            self._remove_pot_creation_date(potfile)

        return potfiles

    @staticmethod
    def _remove_pot_creation_date(path):
        modified_lines = []

        with open(path, "rb") as file:
            for line in file:
                if line.startswith(b'"Report-Msgid-Bugs-To:'):
                    modified_lines.append(b'"Report-Msgid-Bugs-To: elsinga <at> fs.tum.de\\n"')
                if not line.startswith(b'"POT-Creation-Date: '):
                    modified_lines.append(line)

        with open(path, "wb") as file:
            for line in modified_lines:
                file.write(line)
