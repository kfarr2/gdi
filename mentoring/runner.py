import tempfile
import shutil
from django.conf import settings
from django.test.runner import DiscoverRunner

class GDIRunner(DiscoverRunner):
    """
    Creates a temporary directory, runs the tests in there, then deletes it
    """
    def run_tests(self, *args, **kwargs):
        settings.TEST = True
        settings.MEDIA_ROOT = tempfile.mkdtemp(prefix="gdi_unit_test_tmp_dir_")
        super(GDIRunner, self).run_tests(*args, **kwargs)
        shutil.rmtree(settings.MEDIA_ROOT)
        settings.TEST = False
