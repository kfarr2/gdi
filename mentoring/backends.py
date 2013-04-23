import ldap
from djangocas.backends import CASBackend
from django.contrib.auth.models import User, Group
from django.conf import settings as SETTINGS
from django.core.exceptions import PermissionDenied
from django.conf import settings as SETTINGS

class PSUBackend(CASBackend):
    def get_or_init_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # user will have an "unusable" password
            user = User.objects.create_user(username, '')
            user.save()

        # get the user's first and last name
        ld = ldap.initialize(SETTINGS.LDAP_URL)
        ld.simple_bind_s()
        results = ld.search_s(SETTINGS.LDAP_BASE_DN, ldap.SCOPE_SUBTREE, "uid=" + username)
        record = results[0][1]
        cn = record['cn']
        parts = cn[0].split(" ")
        user.first_name = parts[0]
        user.last_name = " ".join(parts[1:])
        mail = record['mail'][0]
        user.email = mail
        user.save()

        return user
