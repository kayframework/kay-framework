# -*- coding: utf-8 -*-
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Kay test management commands.

:Copyright: (c) 2009 Accense Technology, Inc. All rights reserved.
:license: BSD, see LICENSE for more details.
"""

import logging
import os
import sys
import unittest

import kay
kay.setup()
from kay.misc import get_appid

from werkzeug.utils import import_string
from google.appengine.ext import db
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_file_stub
from google.appengine.api import mail_stub
from google.appengine.api import urlfetch_stub
from google.appengine.api.memcache import memcache_stub
from google.appengine.api import user_service_stub
from google.appengine.api.taskqueue import taskqueue_stub
from google.appengine.datastore import datastore_stub_util
try:
  from google.appengine.api.images import images_stub
except ImportError:
  pass

from kay.conf import settings

def setup_env():
  try:
    os.environ['APPLICATION_ID'] = get_appid()
  except Exception:
    fake_appid = os.path.basename(
      os.path.dirname(
        os.path.dirname(
          os.path.dirname(os.path.abspath(__file__)))))
    os.environ['APPLICATION_ID'] = fake_appid
  try:
    os.environ['CURRENT_VERSION_ID'] = get_versionid()
  except Exception:
    # Note: Must have a major and minor version seperated by a '.'
    fake_versionid = "1.1"
    os.environ['CURRENT_VERSION_ID'] = fake_versionid

  os.environ['USER_EMAIL'] = ''
  os.environ['SERVER_NAME'] = 'localhost'
  os.environ['SERVER_PORT'] = '80'
  logging.getLogger().setLevel(logging.ERROR)


def setup_stub(high_replication=False):
  apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
  stub = datastore_file_stub.DatastoreFileStub('test','/dev/null',
                                               '/dev/null', trusted=True)
  if high_replication:
    stub.SetConsistencyPolicy(
        datastore_stub_util.TimeBasedHRConsistencyPolicy())
  apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', stub)

  apiproxy_stub_map.apiproxy.RegisterStub(
    'user', user_service_stub.UserServiceStub())

  apiproxy_stub_map.apiproxy.RegisterStub(
    'memcache', memcache_stub.MemcacheServiceStub())

  apiproxy_stub_map.apiproxy.RegisterStub(
    'urlfetch', urlfetch_stub.URLFetchServiceStub())

  apiproxy_stub_map.apiproxy.RegisterStub(
    'taskqueue', taskqueue_stub.TaskQueueServiceStub())

  try:
    apiproxy_stub_map.apiproxy.RegisterStub(
      'images', images_stub.ImagesServiceStub())
  except NameError:
    pass


def runtest(target='', verbosity=0):
  suite = unittest.TestSuite()
  if target:
    try:
      tests_mod = import_string("%s.tests" % target)
    except Exception:
      tests_mod = import_string(target)
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(
        tests_mod))
  else:
    for app_name in settings.INSTALLED_APPS:
      if app_name.startswith('kay.'):
        continue
      try:
        tests_mod = import_string("%s.tests" % app_name)
      except (ImportError, AttributeError), e:
        logging.error("Loading module %s.tests failed: '%s'." % 
                      (app_name, e))
      else:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(
            tests_mod))
  result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
  sys.exit(int(bool(result.failures or result.errors)))

def do_runtest(target=('t', ''), verbosity=('v', 0),
               high_replication=False):
  """
  Run test for installed applications.
  """
  os.environ['SERVER_SOFTWARE'] = 'Test-Dev'
  setup_env()
  setup_stub(high_replication=high_replication)
  runtest(target, verbosity)

