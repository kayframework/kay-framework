
import os
import logging

from werkzeug import (
  BaseResponse, Request
)

from kay.utils.test import Client
from kay.utils import url_for
from kay.app import get_application
from kay.conf import LazySettings
from kay.ext.testutils.gae_test_base import GAETestBase

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

class ServerErrorTest(GAETestBase):
  """
  Regression test for issue 54 that checks to make sure 
  that responses for error conditions extend BaseResponse.

  http://code.google.com/p/kay-framework/issues/detail?id=54
  """
  def setUp(self):
    s = LazySettings(
      settings_module='kay.tests.regressiontests.server_error_settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)
    self.client.test_logout()

    # Suppress logging error messages
    self._base_logger = logging.getLogger("")
    self._old_logging_handlers = self._base_logger.handlers
    self._base_logger.handlers = [NullHandler()] 

  def tearDown(self):
    self.client.test_logout()
    self._base_logger.handlers = self._old_logging_handlers

  def test_login(self):
    response = self.client.get(url_for('server_error_testapp/index'))
    self.assertEqual(response.status_code, 500)
    self.assertTrue(isinstance(response, BaseResponse))
