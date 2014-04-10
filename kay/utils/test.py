import os
import sys

from werkzeug import Client as WerkZeugClient
from werkzeug import EnvironBuilder

from kay.utils import local
from jinja2 import Template

wrapped = False
render_orig = Template.render

class Client(WerkZeugClient):

  def __init__(self, application, response_wrapper=None, use_cookies=True):
    super(Client, self).__init__(application,
                                 response_wrapper=response_wrapper,
                                 use_cookies=True)
    builder = EnvironBuilder()
    try:
      env = builder.get_environ()
    finally:
      builder.close()
    self.application.app._prepare(env)
    for key, submount_app in self.application.mounts.iteritems():
      if not hasattr(submount_app, 'app_settings') or key == "/_kay":
        continue
      submount_app._prepare(env)

  def test_logout(self, target_url='/', **kwargs):
    self.test_login_or_logout('test_logout', target_url=target_url, **kwargs)
    
  def test_login(self, target_url='/', **kwargs):
    self.test_login_or_logout('test_login', target_url=target_url, **kwargs)

  def open(self, *args, **kw):
    # Copy the kwargs here since we will
    # modify them for passing to EnvironBuilder().
    kwargs = kw.copy()

    # Pop off extra options that open() supports but that
    # will cause EnvironBuilder() to choke.
    as_tuple = kwargs.pop('as_tuple', False)
    buffered = kwargs.pop('buffered', False)
    follow_redirects = kwargs.pop('follow_redirects', False)
    environ = None
    if not kwargs and len(args) == 1:
        if isinstance(args[0], EnvironBuilder):
            environ = args[0].get_environ()
        elif isinstance(args[0], dict):
            environ = args[0]
    if environ is None:
        builder = EnvironBuilder(*args, **kwargs)
        try:
            environ = builder.get_environ()
        finally:
            builder.close()
    
    old_env = os.environ.copy()
    old_cwd = os.getcwd()

    stripped_environ = {}
    for key in environ.keys():
      if isinstance(environ[key], basestring):
        stripped_environ[key] = environ[key]
    try:
        # Add the variables for the current environment to
        # the OS environment to mimic the appengine CGI environment.
        # Don't clear the os.environ since we have set up a number
        # of variables for the environment already. We only want to
        # add variables pertaining to the current request.
        os.environ.update(stripped_environ)
        # Add a dummy value for the appengine specific CGI variable.
        os.environ["PATH_TRANSLATED"] = "main.py"

        # Add additional environment variables like the app id and
        # version number.
        #setup_env()
        # Add the AUTH_DOMAIN
        #os.environ["AUTH_DOMAIN"]

        return super(Client, self).open(*args, **kw)
    finally:
        # Make sure we reset the os environment to the old value.
        os.environ.clear()
        os.environ.update(old_env)

  def test_login_or_logout(self, method, target_url='/', **kwargs):
    auth_backend = None
    for key, submount_app in self.application.mounts.iteritems():
      if not hasattr(submount_app, 'app_settings') or key == "/_kay":
        continue
      if target_url.startswith(key) and hasattr(submount_app, "auth_backend"):
        auth_backend = submount_app.auth_backend
    if auth_backend is None and hasattr(self.application.app, "auth_backend"):
      auth_backend = self.application.app.auth_backend
    if auth_backend is None:
      raise RuntimeError("No suitable auth backend found.")
    try:
      meth = getattr(auth_backend, method)
      meth(self, **kwargs)
    except Exception, e:
      raise
      raise RuntimeError("Failed to invoke %s method with %s,"
                         " reason: %s." % (method, auth_backend, e))

def wrapper(self, *args, **kwargs):
  vars = dict(*args, **kwargs)
  local._used_templates.append(self.name)
  local._used_contexts.append(vars)
  return render_orig(self, *args, **kwargs)

def init_recordings():
  local._used_templates = []
  local._used_contexts = []

def disable_recording():
  init_recordings()
  global wrapped
  if wrapped:
    Template.render = render_orig
    wrapped = False

def init_recording():
  init_recordings()
  global wrapped
  if not wrapped:
    Template.render = wrapper
    wrapped = True

def get_templates():
  if not hasattr(local, '_used_templates'):
    local._used_templates = []
  return local._used_templates

def get_last_template():
  templates = get_templates()
  if templates:
    return templates[-1]

def get_contexts():
  if not hasattr(local, '_used_contexts'):
    local._used_contexts = []
  return local._used_contexts

def get_last_context():
  contexts = get_contexts()
  if contexts:
    return contexts[-1]
