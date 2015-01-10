import os
import datetime
from django.conf import settings as SETTINGS

class LoggingMiddleware(object):
    def process_request(self, request):
        if request.method=="POST":
            with open(os.path.join(SETTINGS.HOME_DIR, 'logs', 'post.log'), 'a') as f:
                items = [
                    datetime.datetime.now(), 
                    request.META.get('REMOTE_ADDR', ''), 
                    request.path, 
                    request.POST
                ]
                f.write("\t".join([str(x) for x in items]) + "\n")
