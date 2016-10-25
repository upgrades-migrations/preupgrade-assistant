from django.contrib.auth.backends import ModelBackend

from ..config.models import AppSettings

class AutologinBackend(ModelBackend):
    """
    Auto authenticate user.
    """

    def authenticate(self, **credentials):
        """
        returns user to be auto-logged in or None
        """
        user_id = AppSettings.get_autologin_user_id()
        return user_id and self.get_user(user_id)

