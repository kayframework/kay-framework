# -*- coding: utf-8 -*-

"""
A sample of kay settings.

:Copyright: (c) 2009 Accense Technology, Inc. 
                     Takashi Matsuo <tmatsuo@candit.jp>,
                     All rights reserved.
:license: BSD, see LICENSE for more details.
"""

DEBUG = False
ROOT_URL_MODULE = 'kay.tests.globalurls'

INSTALLED_APPS = (
  'kay.ext.live_settings',
)

APP_MOUNT_POINTS = {
  'kay.ext.live_settings': '/_kay/livesettings/admin',
}

# You can remove following settings if unnecessary.
CONTEXT_PROCESSORS = (
  'kay.context_processors.request',
  'kay.context_processors.url_functions',
  'kay.context_processors.media_url',
)
