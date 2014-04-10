# -*- coding: utf-8 -*-

"""
A urls module that raises a DeadlineExceededError

:Copyright: (c) 2010 Ian Lewis <IanMLewis@gmail.com> All rights reserved.
:license: BSD, see LICENSE for more details.
"""

from google.appengine.runtime import DeadlineExceededError

raise DeadlineExceededError()
