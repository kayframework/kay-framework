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
    Rule('/', endpoint='index', view='kay.tests.views.index'),
    Rule('/countup', endpoint='countup', view='kay.tests.views.countup'),
    Rule('/index2', endpoint='index2', view='kay.tests.views.index2'),
    Rule('/no_decorator', endpoint='no_decorator',
         view='kay.tests.views.no_decorator'),
    Rule('/class_based_test_root/', endpoint='maintenance_check',
         view=('kay.tests.views.MaintenanceCheck',(), {})),
    Rule('/class_based_test_root/index2',
         endpoint='maintenance_check_with_arg',
         view=('kay.tests.views.MaintenanceCheckWithArgument',(), {})),
    Rule('/oldpage', endpoint='oldpage', redirect_to='newpage',
         view='kay.tests.views.oldpage'),
    Rule('/newpage', endpoint='newpage', view='kay.tests.views.newpage'),
    Rule('/cron', endpoint='cron', view='kay.tests.views.cron'),
    Rule('/class_based_test_root/cron', endpoint='cron_only',
         view=('kay.tests.views.CronOnly', (), {})),
  )
]
