
from werkzeug import (
  BaseResponse, Request
)

from kay.app import get_application
from kay.conf import LazySettings
from kay.ext.testutils.gae_test_base import GAETestBase
from kay.utils.test import Client

class SessionMiddlewareTestCase(GAETestBase):
  KIND_NAME_UNSWAPPED = False
  USE_PRODUCTION_STUBS = True
  CLEANUP_USED_KIND = True

  def setUp(self):
    s = LazySettings(settings_module='kay.tests.settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)

  def tearDown(self):
    pass

  def test_countup(self):
    response = self.client.get('/countup')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data, '1')
    response = self.client.get('/countup')
    self.assertEqual(response.data, '2')
    response = self.client.get('/countup')
    self.assertEqual(response.data, '3')
    response = self.client.get('/countup')
    self.assertEqual(response.data, '4')
    response = self.client.get('/countup')
    self.assertEqual(response.data, '5')

class SessionMiddlewareOnCookieWithSecureAttributeTestCase(GAETestBase):
  KIND_NAME_UNSWAPPED = False
  USE_PRODUCTION_STUBS = True
  CLEANUP_USED_KIND = True

  def setUp(self):
    import os
    s = LazySettings(settings_module='kay.tests.cookie_session_settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)
    self.server_name = os.environ['SERVER_NAME']

  def tearDown(self):
    pass

  def test_if_cookie_is_marked_as_secure(self):
    url = 'https://%s/countup' % self.server_name
    response = self.client.get('/countup', url)
    self.assert_('secure' in response.headers['Set-Cookie'],
                 'The Set-Cookie header does not contain secure flag.')


class SessionMiddlewareWithSecureCookieTestCase(GAETestBase):
  KIND_NAME_UNSWAPPED = False
  USE_PRODUCTION_STUBS = True
  CLEANUP_USED_KIND = True

  def setUp(self):
    s = LazySettings(settings_module='kay.tests.securecookie_session_settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)

  def tearDown(self):
    pass

  def test_countup(self):
    response = self.client.get('/countup')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data, '1')
    response = self.client.get('/countup')
    self.assertEqual(response.data, '2')
    response = self.client.get('/countup')
    self.assertEqual(response.data, '3')
    response = self.client.get('/countup')
    self.assertEqual(response.data, '4')
    response = self.client.get('/countup')
    self.assertEqual(response.data, '5')
