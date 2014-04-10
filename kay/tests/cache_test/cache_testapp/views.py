# -*- coding: utf-8 -*-

"""
Kay cache test views.

:Copyright: (c) 2012 Takashi Matsuo <matsuo.takashi@gmail.com>
  All rights reserved.
:license: BSD, see LICENSE for more details.
"""

from werkzeug import (
  Response,
)

from kay.cache.decorators import cache_page
from kay.handlers import BaseHandler
from kay.utils import (
  render_to_response,
)

def index(request):
  return Response("Testing Cache")

@cache_page(cache_timeout=3600, namespace="CACHE_DECORATOR",
            cache_anonymous_only=True)
def decorator(request):
  return Response("Testing Cache")


class CacheHandler(BaseHandler):
  @cache_page(cache_timeout=3600, namespace="CACHE_DECORATOR",
              cache_anonymous_only=True)
  def get(self):
    return Response("Testing cache decorator with class based view")
