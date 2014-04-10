# -*- coding: utf-8 -*-

"""
Kay test urls.

:Copyright: (c) 2009 Takashi Matsuo <tmatsuo@candit.jp> All rights reserved.
:license: BSD, see LICENSE for more details.
"""

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/', endpoint='index',
         view='kay.tests.stacked_decorators.views.index'),
    Rule('/class', endpoint='MyView',
         view=('kay.tests.stacked_decorators.views.MyView', (), {})),
    Rule('/ndb', endpoint='ndb',
         view='kay.tests.stacked_decorators.views.ndb'),
    Rule('/class_ndb', endpoint='MyNDBView',
         view=('kay.tests.stacked_decorators.views.MyNDBView', (), {})),
  )
]
