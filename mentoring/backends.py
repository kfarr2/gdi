import ldap
from django_cas.backends import CASBackend
from django.contrib.auth.models import User, Group
from django.conf import settings as SETTINGS
from django.core.exceptions import PermissionDenied

class PSUBackend(CASBackend):
    def get_or_init_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # user will have an "unusable" password
            user = User.objects.create_user(username, '')
            user.save()

        return user
