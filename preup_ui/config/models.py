from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import models

import json

class AppSettings(models.Model):
    """
    settings stored in DB

    for bools, value is either 'T' or 'F'
    """
    key = models.CharField(max_length=32, blank=False, null=False)
    value = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "%s = '%s'" % (self.key, self.value)

    @classmethod
    def get_initial_state_filter(cls):
        """tests with these states should be displayed initially"""
        # TODO: when content is invalid, reset it to default _valid_ value
        try:
            value = cls.objects.get(key="STATES_FILTER").value
        except ObjectDoesNotExist:
            pass
        except MultipleObjectsReturned:
            pass
        except Exception:
            pass
        else:
            if value:
                try:
                    return json.loads(value)
                except ValueError:
                    pass
        s = cls.set_initial_state_filter(["fail", "needs_action", "needs_inspection", "fixed", "pass", "informational"])
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
    def get_disable_auth(cls):
        """
        If there is record in DB, return True if value == 'T', False otherwise

        If there is no record, return None.
        """
        try:
            val = cls.objects.get(key="DISABLE_AUTH").value
            return val == 'T'
        except (MultipleObjectsReturned, ObjectDoesNotExist, AttributeError):
            return None

    @classmethod
    def set_disable_auth(cls, value):
        """ value is either True or False """
        db_value = 'T' if value else 'F'
        cls.objects.filter(key="DISABLE_AUTH").delete()
        s = cls(key="DISABLE_AUTH", value=db_value)
        s.save()
        return s

    @classmethod
    def get_disable_local_auth(cls):
        """
        If there is record in DB, return True if value == 'T', False otherwise

        If there is no record, return None.
        """
        try:
            val = cls.objects.get(key="DISABLE_LOCAL_AUTH").value
        except (MultipleObjectsReturned, ObjectDoesNotExist, AttributeError):
            val = cls.set_disable_local_auth(False).value
        return val == 'T'

    @classmethod
    def set_disable_local_auth(cls, value):
        """ value is either True or False """
        db_value = 'T' if value else 'F'
        cls.objects.filter(key="DISABLE_LOCAL_AUTH").delete()
        s = cls(key="DISABLE_LOCAL_AUTH", value=db_value)
        s.save()
        return s