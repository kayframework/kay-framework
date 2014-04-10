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
         view='kay.tests.auth_testapp.views.index'),
    Rule('/secret', endpoint='secret',
         view='kay.tests.auth_testapp.views.secret'),
    Rule('/c/secret', endpoint='c_secret',
         view=('kay.tests.auth_testapp.views.SecretHandler', (), {})),
  )
]
