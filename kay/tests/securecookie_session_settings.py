# -*- coding: utf-8 -*-

"""
Kay test settings.

:Copyright: (c) 2009 Takashi Matsuo <tmatsuo@candit.jp> All rights reserved.
:license: BSD, see LICENSE for more details.
"""

DEBUG = False
ROOT_URL_MODULE = 'kay.tests.globalurls'

MIDDLEWARE_CLASSES = (
  'kay.sessions.middleware.SessionMiddleware',
)
SESSION_STORE = 'kay.sessions.sessionstore.SecureCookieSessionStore'

INSTALLED_APPS = (
  'kay.tests',
)

APP_MOUNT_POINTS = {
  'kay.tests': '/',
}
