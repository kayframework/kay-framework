
import os

from google.appengine.runtime import DeadlineExceededError

from werkzeug import (
  BaseResponse, Request
)

from kay.utils.test import Client
from kay.app import get_application
from kay.conf import LazySettings
from kay.ext.testutils.gae_test_base import GAETestBase

class BadUrlsTestCase(GAETestBase):
  def setUp(self):
    s = LazySettings(
      settings_module='kay.tests.regressiontests.badurls_settings')
    self.app = get_application(settings=s)
    try:
        self.client = Client(self.app, BaseResponse)
    except DeadlineExceededError:
        pass

  def test_bad_url_map_load(self):
    self.assertFalse(getattr(self.app.app, 'url_map', None))
