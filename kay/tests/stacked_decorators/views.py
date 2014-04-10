from werkzeug import (
  unescape, redirect, Response,
)
from google.appengine.ext.ndb import tasklets

from kay.handlers import BaseHandler
from kay.cache.decorators import no_cache
from kay.auth.decorators import login_required

@login_required
@no_cache
def index(request):
  return Response("OK")


class MyView(BaseHandler):
  @login_required
  @no_cache
  def get(self):
    return Response("OK")

@no_cache
@tasklets.toplevel
def ndb(request):
  return Response("OK")

class MyNDBView(BaseHandler):
  @no_cache
  @tasklets.toplevel
  def get(self):
    return Response("OK")

