
import os

from google.appengine.api import memcache

from werkzeug import (
  BaseResponse, Request
)

from kay.utils import url_for
from kay.utils.test import Client
from kay.app import get_application
from kay.conf import LazySettings
from kay.ext.testutils.gae_test_base import GAETestBase

class CacheTestCase(GAETestBase):
  def setUp(self):
    s = LazySettings(settings_module='kay.tests.cache_test.settings')
    self.app = get_application(settings=s)
    self.client = Client(self.app, BaseResponse)
    memcache.flush_all()
    
  def test_cache_middleware(self):
    # make sure that CACHE_MIDDLEWARE_ANONYMOUSE_ONLY works
    self.client.test_login(email='user@example.com')
    response = self.client.get(url_for('cache_testapp/index'))
    self.assertEqual(response.status_code, 200)
    c = memcache.get('http://localhost/?lang=en', namespace='CACHE_MIDDLEWARE')
    self.assertEqual(c, None)
    self.client.test_logout()
    # user logout, so the cache works
    response = self.client.get(url_for('cache_testapp/index'))
    self.assertEqual(response.status_code, 200)
    c = memcache.get('http://localhost/?lang=en', namespace='CACHE_MIDDLEWARE')
    self.assertEqual(c.data, response.data)

  def test_cache_decorator_with_function_view(self):
    # make sure that CACHE_MIDDLEWARE_ANONYMOUSE_ONLY works
    self.client.test_login(email='user@example.com')
    response = self.client.get(url_for('cache_testapp/decorator'))
    self.assertEqual(response.status_code, 200)
    c = memcache.get('http://localhost/decorator?lang=en',
                     namespace='CACHE_DECORATOR')
    self.assertEqual(c, None)
    self.client.test_logout()
    # user logout, so the cache works
    response = self.client.get(url_for('cache_testapp/decorator'))
    self.assertEqual(response.status_code, 200)
    c = memcache.get('http://localhost/decorator?lang=en',
                     namespace='CACHE_DECORATOR')
    self.assertEqual(c.data, response.data)

  def test_cache_decorator_with_class_view(self):
    # make sure that CACHE_MIDDLEWARE_ANONYMOUSE_ONLY works
    self.client.test_login(email='user@example.com')
    response = self.client.get(url_for('cache_testapp/decorator_class'))
    self.assertEqual(response.status_code, 200)
    c = memcache.get('http://localhost/decorator_class?lang=en',
                     namespace='CACHE_DECORATOR')
    self.assertEqual(c, None)
    self.client.test_logout()
    # user logout, so the cache works
    response = self.client.get(url_for('cache_testapp/decorator_class'))
    self.assertEqual(response.status_code, 200)
    c = memcache.get('http://localhost/decorator_class?lang=en',
                     namespace='CACHE_DECORATOR')
    self.assertEqual(c.data, response.data)
