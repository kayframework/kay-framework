# -*- coding: utf-8 -*-
# live_settings.urls
# 

# Following few lines is an example urlmapping with an older interface.
"""
from werkzeug.routing import EndpointPrefix, Rule

def make_rules():
  return [
    EndpointPrefix('live_settings/', [
      Rule('/', endpoint='index'),
    ]),
  ]

all_views = {
  'live_settings/index': 'live_settings.views.index',
}
"""

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/admin', endpoint='admin', view='kay.ext.live_settings.views.admin'),
  )
]

