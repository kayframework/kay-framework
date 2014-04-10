
import os
import logging
from time import sleep

from werkzeug import (
  BaseResponse, Request
)

from google.appengine.api import memcache

from kay.utils.test import Client
from kay.utils import url_for
from kay.app import get_application
from kay.conf import LazySettings
from kay.ext.testutils.gae_test_base import GAETestBase

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

class EReporterTest(GAETestBase):
  def setUp(self):
    s = LazySettings(
      settings_module='kay.tests.ereporter_settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)
    #self.client.test_logout()

    # Suppress logging error messages
    self._base_logger = logging.getLogger("")
    self._old_logging_handlers = self._base_logger.handlers
    self._base_logger.handlers = filter(
        lambda h: not isinstance(h, logging.StreamHandler),
        self._old_logging_handlers,
    ) 

  def tearDown(self):
    self.client.test_logout()
    self._base_logger.handlers = self._old_logging_handlers

  def test_ereporter(self):
    from kay.ext.ereporter.models import ExceptionRecord
    self.assertEqual(ExceptionRecord.all().count(), 0, "ExceptionRecord objects already exist!")

    response = self.client.get(url_for('ereporter_testapp/index'))
    self.assertEqual(response.status_code, 500, "Expected 500 error code.")
    self.assertEqual(ExceptionRecord.all().count(), 1)

    # Simulate the key expiring.
    memcache.flush_all();

    response = self.client.get(url_for('ereporter_testapp/index'))
    self.assertEqual(response.status_code, 500, "Expected 500 error code.")
    self.assertEqual(ExceptionRecord.all().count(), 1, "More than one ExceptionRecord object was created!")
    self.assertEqual(ExceptionRecord.all()[0].count, 2, "ExceptionRecord count not incremented!")
