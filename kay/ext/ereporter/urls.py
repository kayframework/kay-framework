# -*- coding: utf-8 -*-
# ereporter.urls
# 

# Following few lines is an example urlmapping with an older interface.
"""
from werkzeug.routing import EndpointPrefix, Rule

def make_rules():
  return [
    EndpointPrefix('ereporter/', [
      Rule('/', endpoint='index'),
    ]),
  ]

all_views = {
  'ereporter/index': 'ereporter.views.index',
}
"""

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/', endpoint='report_generator', view='kay.ext.ereporter.views.report_generator'),
    Rule('/admin', endpoint='admin', view='kay.ext.ereporter.views.report_admin'),
  )
]
