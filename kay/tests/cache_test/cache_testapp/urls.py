# -*- coding: utf-8 -*-

"""
Kay gaema test urls.

:Copyright: (c) 2009 Takashi Matsuo <tmatsuo@candit.jp> All rights reserved.
:license: BSD, see LICENSE for more details.
"""

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/', endpoint='index',
         view='kay.tests.cache_test.cache_testapp.views.index'),
    Rule('/decorator', endpoint='decorator',
         view='kay.tests.cache_test.cache_testapp.views.decorator'),
    Rule('/decorator_class', endpoint='decorator_class',
         view=('kay.tests.cache_test.cache_testapp.views.CacheHandler',
               (), {})),
  )
]
