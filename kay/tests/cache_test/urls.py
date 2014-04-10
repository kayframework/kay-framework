# -*- coding: utf-8 -*-

"""
Kay URL dispatch setting.
"""

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/_ah/queue/deferred', endpoint='deferred',
         view='kay.handlers.task.task_handler'),
    Rule('/maintenance_page', endpoint='_internal/maintenance_page',
         view='kay._internal.views.maintenance_page'),
  )
]
