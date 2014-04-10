#!/usr/bin/env python2.5
# -*- coding:utf-8 -*-

"""
AppStatsMiddleware adapted to Kay framework.

:Copyright: (c) 2010 Ian Lewis <ianmlewis@gmail.com>,
:license: BSD, see LICENSE for more details.
"""

from kay.conf import settings

class AppStatsMiddleware(object):
  """
  Middleware to enable appstats recording.

  Based off of the the AppstatsDjangoMiddleware in the 
  Appengine SDK
  """

  def _record_ok(self, request):
    if 'kay.ext.live_settings' in settings.INSTALLED_APPS:
      from kay.ext.live_settings import live_settings
      record_ok = live_settings.get("kay.ext.appstats.middleware", "on")
      request._appstats_record = (record_ok.lower() == "on")
      return request._appstats_record
    else:
      return True

  def process_request(self, request):
    """
    Called by Kay before deciding which view to execute.
    """
    if self._record_ok(request):
      from google.appengine.ext.appstats.recording import start_recording
      start_recording()

  def process_response(self, request, response):
    """
    Stops recording. Optionally sets some extension data for
    FirePython.
    """
    if getattr(request, '_appstats_record', True):
      from google.appengine.ext.appstats.recording import end_recording
  
      firepython_set_extension_data = getattr(
        request,
        'firepython_set_extension_data',
        None)
      end_recording(response.status_code, firepython_set_extension_data)
    return response
