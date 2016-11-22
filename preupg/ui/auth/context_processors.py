from preupg.ui.config.models import AppSettings

def auth_enabled(request):
    return {'auth_enabled': AppSettings.get_autologin_user_id() is None}

