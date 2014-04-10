# -*- coding: utf-8 -*-
# server_error_testapp.urls
# 

# Following few lines is an example urlmapping with an older interface.
"""
from werkzeug.routing import EndpointPrefix, Rule

def make_rules():
  return [
    EndpointPrefix('server_error_testapp/', [
      Rule('/', endpoint='index'),
    ]),
  ]

all_views = {
  'server_error_testapp/index': 'server_error_testapp.views.index',
}
"""

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/', endpoint='index', view='kay.tests.regressiontests.server_error_testapp.views.index'),
  )
]

