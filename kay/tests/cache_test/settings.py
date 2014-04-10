# -*- coding: utf-8 -*-

"""
Kay test settings.

:Copyright: (c) 2009 Takashi Matsuo <tmatsuo@candit.jp> All rights reserved.
:license: BSD, see LICENSE for more details.
"""

DEBUG = False
ROOT_URL_MODULE = 'kay.tests.cache_test.urls'

MIDDLEWARE_CLASSES = (
  'kay.auth.middleware.AuthenticationMiddleware',
  'kay.cache.middleware.CacheMiddleware',
)

INSTALLED_APPS = (
  'kay.tests.cache_test.cache_testapp',
)

APP_MOUNT_POINTS = {
  'kay.tests.cache_test.cache_testapp': '/',
}
CACHE_MIDDLEWARE_SECONDS = 3600
CACHE_MIDDLEWARE_NAMESPACE = 'CACHE_MIDDLEWARE'
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

USE_I18N = True
