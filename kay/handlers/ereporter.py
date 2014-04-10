# -*- coding: utf-8 -*-

"""
kay.handlers.ereporter

Wrapper handler for the ereporter

:Copyright: (c) 2009 Takashi Matsuo <tmatsuo@candit.jp> All rights reserved.
:license: BSD, see LICENSE for more details.
"""

from google.appengine.ext.ereporter import report_generator

import kay
kay.setup()

main = report_generator.main
