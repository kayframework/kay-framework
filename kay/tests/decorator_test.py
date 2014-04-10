#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Kay decorator test.

:Copyright: (c) 2009 Takashi Matsuo <tmatsuo@candit.jp> All rights reserved.
:license: BSD, see LICENSE for more details.
"""

import unittest
import re

from google.appengine.api import apiproxy_stub_map
from google.appengine.api.capabilities import capability_stub
from google.appengine.api import datastore_file_stub
from google.appengine.api import urlfetch_stub
from google.appengine.api.memcache import memcache_stub
from google.appengine.api import user_service_stub

from werkzeug import BaseResponse, Request

import kay
from kay.app import get_application
from kay.conf import LazySettings
from kay.ext.testutils.gae_test_base import GAETestBase
from kay.tests import capability_stub as mocked_capability_stub
from kay.utils.test import Client

class MaintenanceCheckTestCase(unittest.TestCase):
  
  def setUp(self):
    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    stub = datastore_file_stub.DatastoreFileStub('test','/dev/null',
                                                 '/dev/null')
    apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', stub)

    apiproxy_stub_map.apiproxy.RegisterStub(
      'user', user_service_stub.UserServiceStub())

    apiproxy_stub_map.apiproxy.RegisterStub(
      'memcache', memcache_stub.MemcacheServiceStub())

    apiproxy_stub_map.apiproxy.RegisterStub(
      'urlfetch', urlfetch_stub.URLFetchServiceStub())

    s = LazySettings(settings_module='kay.tests.settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)
    if apiproxy_stub_map.apiproxy\
          ._APIProxyStubMap__stub_map.has_key('capability_service'):
      del(apiproxy_stub_map.apiproxy\
            ._APIProxyStubMap__stub_map['capability_service'])

  def tearDown(self):
    pass

  def test_success(self):
    """Test with normal CapabilityServiceStub"""
    apiproxy_stub_map.apiproxy.RegisterStub(
      'capability_service',
      capability_stub.CapabilityServiceStub())
    response = self.client.get('/')
    self.assertEqual(response.status_code, 200)
    response = self.client.get('/class_based_test_root/')
    self.assertEqual(response.status_code, 200)

  def test_failure(self):
    """Test with DisabledCapabilityServiceStub
    """
    apiproxy_stub_map.apiproxy.RegisterStub(
      'capability_service',
      mocked_capability_stub.DisabledCapabilityServiceStub())
    response = self.client.get('/')
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response.headers['Location'],
                     'http://localhost/maintenance_page')

    response = self.client.get('/class_based_test_root/')
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response.headers['Location'],
                     'http://localhost/maintenance_page')

    response = self.client.get('/index2')
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response.headers['Location'],
                     'http://localhost/no_decorator')

    response = self.client.get('/class_based_test_root/index2')
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response.headers['Location'],
                     'http://localhost/no_decorator')

    response = self.client.get('/no_decorator')
    self.assertEqual(response.status_code, 200)

class CronOnlyTestCase(GAETestBase):

  def setUp(self):
    s = LazySettings(settings_module='kay.tests.settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)

  def test_cron_only(self):
    response = self.client.get("/cron",
            headers=(('X-AppEngine-Cron', 'true'),))
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.data == "OK")
    response = self.client.get("/class_based_test_root/cron",
            headers=(('X-AppEngine-Cron', 'true'),))
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.data == "OK")

  def test_cron_only_failure(self):
    response = self.client.get("/cron")
    self.assertEqual(response.status_code, 403)
    response = self.client.get("/class_based_test_root/cron")
    self.assertEqual(response.status_code, 403)


class CronOnlyDebugTestCase(GAETestBase):

  def setUp(self):
    s = LazySettings(settings_module='kay.tests.settings')
    s.DEBUG = True
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)

  def test_cron_only_failure(self):
    from kay.utils import is_dev_server
    response = self.client.get("/cron")
    if is_dev_server():
      self.assertEqual(response.status_code, 200)
    else:
      self.assertEqual(response.status_code, 403)
    response = self.client.get("/class_based_test_root/cron")
    if is_dev_server():
      self.assertEqual(response.status_code, 200)
    else:
      self.assertEqual(response.status_code, 403)

  def test_cron_only(self):
    response = self.client.get("/cron",
            headers=(('X-AppEngine-Cron', 'true'),))
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.data == "OK")
    response = self.client.get("/class_based_test_root/cron",
            headers=(('X-AppEngine-Cron', 'true'),))
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.data == "OK")


class StackedDecoratorsTestCase(GAETestBase):

  def setUp(self):
    s = LazySettings(settings_module='kay.tests.stacked_decorators.settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)

  def test_stacked_decorators(self):
    self.client.test_login(email='user@example.com')
    response = self.client.get('/')
    self.assertEqual(response.status_code, 200)
    response = self.client.get('/class')
    self.assertEqual(response.status_code, 200)
    response = self.client.get('/ndb')
    self.assertEqual(response.status_code, 200)
    response = self.client.get('/class_ndb')
    self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
  unittest.main()
