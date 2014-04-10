# -*- coding: utf-8 -*-


from werkzeug import (
  BaseResponse, Client, Request
)
from google.appengine.ext.appstats import recording

from kay.app import get_application
from kay.conf import LazySettings
from kay.ext.testutils.gae_test_base import GAETestBase
from kay.ext.appstats.middleware import AppStatsMiddleware

class AppStatsMiddlewareTestCase(GAETestBase):
  KIND_NAME_UNSWAPPED = False
  USE_PRODUCTION_STUBS = True
  CLEANUP_USED_KIND = True

  def setUp(self):
    from google.appengine.api import memcache
    memcache.flush_all()
    s = LazySettings(settings_module='kay.tests.appstats_settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)

  def tearDown(self):
    pass

  def test_appstats_middleware(self):

    request = Request({})
    middleware = AppStatsMiddleware()

    r = middleware.process_request(request)
    self.assertTrue(r is None)

    r = middleware.process_response(request, BaseResponse("", 200))
    self.assertTrue(isinstance(r, BaseResponse))

    summary = recording.load_summary_protos()
    self.assert_(summary)

  def test_appstats_middleware_request(self):

    response = self.client.get('/no_decorator')
    summary = recording.load_summary_protos()
    self.assert_(summary)
