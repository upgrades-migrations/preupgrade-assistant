from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test


def first_run_required(function=None):
    """
    Decorator for views that are only available if there is no existing user.
    """
    actual_decorator = user_passes_test(
        lambda u: get_user_model().objects.count() == 0,
        login_url='/',
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

