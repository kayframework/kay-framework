# -*- coding: utf-8 -*-

"""
Kay authentication backend with user information stored in the
datastore.

:Copyright: (c) 2009 Accense Technology, Inc. 
                     Takashi Matsuo <tmatsuo@candit.jp>,
                     All rights reserved.
:license: BSD, see LICENSE for more details.
"""

from google.appengine.ext import db
from werkzeug.urls import url_quote_plus
from werkzeug.utils import import_string

from kay.exceptions import ImproperlyConfigured
from kay.conf import settings
from kay.utils import (
  local, url_for
)
from kay.auth.models import AnonymousUser
from kay.misc import get_appid


class DatastoreBackend(object):
  def __init__(self):
    # avoid 'no implementation for kind' error.
    import_string(settings.AUTH_USER_MODEL)
    if not 'kay.sessions.middleware.SessionMiddleware' in \
          settings.MIDDLEWARE_CLASSES:
      raise ImproperlyConfigured(
        "The DatastoreBackend requires session middleware to "
        "be installed. Edit your MIDDLEWARE_CLASSES setting to insert "
        "'kay.sessions.middleware.SessionMiddleware'.")
  
  def get_user(self, request):
    if request.session.has_key('_user'):
      session_user = request.session['_user']
      if isinstance(session_user, db.Key):
        # keep compatibility with the old way of storing user keys:
        return db.get(session_user)
      else:
        auth_model_class = import_string(settings.AUTH_USER_MODEL)
        return auth_model_class.get_by_user_name(session_user)
    else:
      return AnonymousUser()

  def create_login_url(self, url):
    return url_for("auth/login", next=url_quote_plus(url))

  def create_logout_url(self, url):
    return url_for("auth/logout", next=url_quote_plus(url))

  def store_user(self, user):
    from kay.sessions import renew_session
    renew_session(local.request)
    local.request.session['_user'] = user.user_name
    return True

  def login(self, request, user_name, password):
    try:
      auth_model_class = import_string(settings.AUTH_USER_MODEL)
    except (ImportError, AttributeError), e:
      raise ImproperlyConfigured, \
          'Failed to import %s: "%s".' % (settings.AUTH_USER_MODEL, e)
    user = auth_model_class.get_by_user_name(user_name)
    if user is None:
      return False
    if user.check_password(password):
      return self.store_user(user)
    return False

  def test_login_or_logout(self, client, username=''):
    from cookielib import Cookie
    args = [None, None, '', None, None, '/', None, None, 86400, None, None,
            None, None]
    try:
      auth_model_class = import_string(settings.AUTH_USER_MODEL)
    except (ImportError, AttributeError), e:
      raise ImproperlyConfigured, \
          'Failed to import %s: "%s".' % (settings.AUTH_USER_MODEL, e)
    user = auth_model_class.get_by_user_name(username)
    session_store = import_string(settings.SESSION_STORE)()
    data = None
    for cookie in client.cookie_jar:
      if cookie.name == settings.COOKIE_NAME:
        data = cookie.value
    if data is None:
      session = session_store.new()
    else:
      session = session_store.get(data)
    if user:
      session['_user'] = user.key()
    elif session.has_key('_user'):
      del session['_user']
    session_store.save(session)
    data = "\"%s\"" % session_store.get_data(session)
    client.cookie_jar.set_cookie(Cookie(1, settings.COOKIE_NAME,
                                        data,
                                        *args))
    
  def test_login(self, client, username=''):
    self.test_login_or_logout(client, username)

  def test_logout(self, client):
    self.test_login_or_logout(client, '')

class DatastoreBackendWithOwnedDomainHack(DatastoreBackend):

  def store_user(self, user):
    from kay.auth.models import TemporarySession
    session = TemporarySession.get_new_session(user)
    return session

  def create_login_url(self, url):
    import os
    hostname = get_appid() + '.appspot.com'
    url = url_for("auth/login",
                  next=url_quote_plus(url),
                  original_host_url=url_quote_plus(local.request.host_url),
                  owned_domain_hack=True)
    if 'SERVER_SOFTWARE' in os.environ and \
          os.environ['SERVER_SOFTWARE'].startswith('Dev'):
      return url
    else:
      return "https://%s%s" % (hostname, url)
