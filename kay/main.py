# -*- coding: utf-8 -*-

"""
Kay main handler script.

:Copyright: (c) 2009 Accense Technology, Inc. All rights reserved.
:license: BSD, see LICENSE for more details.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import kay
kay.setup()

from kay.app import get_application

application = get_application()
