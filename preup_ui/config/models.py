from django.contrib.auth import get_user_model
from django.db import models

import json

class AppSettings(models.Model):
    """
    settings stored in DB

    for bools, value is either 'T' or 'F'
    """
    key = models.CharField(max_length=32, primary_key=True)
    value = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "%s = '%s'" % (self.key, self.value)

    @classmethod
    def get_initial_state_filter(cls):
        """tests with these states should be displayed initially"""
        # TODO: when content is invalid, reset it to default _valid_ value
        try:
            value = cls.objects.get(key="STATES_FILTER").value
        except Exception:
            pass
        else:
            if value:
                try:
                    return json.loads(value)
                except ValueError:
                    pass
        s = cls.set_initial_state_filter(["error", "fail", "needs_action", "needs_inspection", "fixed", "pass", "informational"])
        return json.loads(s.value)

    @classmethod
    def set_initial_state_filter(cls, value):
        """
        tests with these states should be displayed initially
        value: list of states [fail, error, ...]
        """
        try:
            json_value = json.dumps(value)
        except TypeError:
            json_value = json.dumps(list(value))
        # remove all previous filters
        cls.objects.filter(key="STATES_FILTER").delete()
        #set new one
        s = cls(key="STATES_FILTER", value=json_value)
        s.save()
        return s

    @classmethod
    def get_autologin_user_id(cls):
        """ returns user to be auto-logged in """
        try:
            return int(cls.objects.get(key="AUTOLOGIN_USER").value)
        except cls.DoesNotExist:
            return None

    @classmethod
    def set_autologin_user_id(cls, user_id):
        """ sets user to be auto-logged in """
        cls(key="AUTOLOGIN_USER", value=str(user_id)).save()

    @classmethod
    def unset_autologin_user_id(cls):
        """ unsets user to be auto-logged in """
        cls.objects.filter(key="AUTOLOGIN_USER").delete()

