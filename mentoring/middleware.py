import os
import datetime
from django.conf import settings as SETTINGS

class LoggingMiddleware(object):
    def process_request(self, request):
        if request.POST:
            with open(os.path.join(SETTINGS.HOME_DIR, 'logs', 'post.log'), 'a') as f:
                f.write(str(datetime.datetime.now()) + "\t" + str(request.path) + "\t" + str(request.POST) + "\n")
