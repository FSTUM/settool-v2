from django.contrib.auth.tokens import PasswordResetTokenGenerator


class TokenGenerator(PasswordResetTokenGenerator):
    @staticmethod
    def _make_hash_value(user, timestamp):
        return str(user.pk) + str(timestamp)


account_activation_token = TokenGenerator()
