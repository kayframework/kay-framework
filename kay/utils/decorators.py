# -*- coding: utf-8 -*-

"""
kay.utils.decorators
~~~~~~~~~~~~~~~~~~~~

This module implements useful decorators for appengine datastore.

:Copyright: (c) 2009 Accense Technology, Inc.,
                     Takashi Matsuo <tmatsuo@candit.jp>,
                     Ian Lewis <IanMLewis@gmail.com>,
                     All rights reserved.
:license: BSD, see LICENSE for more details.
"""

import logging
import types
from functools import wraps, update_wrapper, partial
from google.appengine.api import memcache
from werkzeug._internal import _missing
from kay.handlers import BaseHandler

DATASTORE_WRITABLE = "appengine_datastore_writable"

# Functions that help with dynamically creating decorators for views.
# Taken from django.

class MethodDecoratorAdaptor(object):
  """
  Generic way of creating decorators that adapt to being
  used on methods
  """
  def __init__(self, decorator, func):
    update_wrapper(self, func)
    # NB: update the __dict__ first, *then* set
    # our own .func and .decorator, in case 'func' is actually
    # another MethodDecoratorAdaptor object, which has its
    # 'func' and 'decorator' attributes in its own __dict__
    self.decorator = decorator
    self.func = func
  def __call__(self, *args, **kwargs):
    return self.decorator(self.func)(*args, **kwargs)
  def __get__(self, instance, owner):
    func = self.decorator(request_handler(self.func.__get__(instance, owner)))
    if isinstance(instance, BaseHandler):
        func = partial(func, instance.request)
    return func

def request_handler(func):
  def inner(request, *args, **kwargs):
    if hasattr(func, 'im_self') and isinstance(func.im_self, BaseHandler):
        return func(**kwargs)
    else:
      return func(request, **kwargs)
  return inner
        
    
def auto_adapt_to_methods(decorator):
  """
  Takes a decorator function, and returns a decorator-like callable that can
  be used on methods as well as functions.
  """
  def adapt(func):
    return MethodDecoratorAdaptor(decorator, func)
  return wraps(decorator)(adapt)

def decorator_from_middleware_with_args(middleware_class):
  """
  Like decorator_from_middleware, but returns a function
  that accepts the arguments to be passed to the middleware_class.
  Use like::

     cache_page = decorator_from_middleware_with_args(CacheMiddleware)
     # ...

     @cache_page(3600)
     def my_view(request):
       # ...
  """
  return make_middleware_decorator(middleware_class)

def decorator_from_middleware(middleware_class):
  """
  Given a middleware class (not an instance), returns a view decorator. This
  lets you use middleware functionality on a per-view basis. The middleware
  is created with no params passed.
  """
  return make_middleware_decorator(middleware_class)()

def make_middleware_decorator(middleware_class):
  def _make_decorator(*m_args, **m_kwargs):
    middleware = middleware_class(*m_args, **m_kwargs)
    def _decorator(view_func):
      def _wrapped_view(request, **kwargs):
        if hasattr(middleware, 'process_request'):
          result = middleware.process_request(request)
          if result is not None:
            return result
        if hasattr(middleware, 'process_view'):
          result = middleware.process_view(request, view_func, **kwargs)
          if result is not None:
            return result
        try:
          response = view_func(request, **kwargs)
        except Exception, e:
          if hasattr(middleware, 'process_exception'):
            result = middleware.process_exception(request, e)
            if result is not None:
              return result
          raise
        if hasattr(middleware, 'process_response'):
          result = middleware.process_response(request, response)
          if result is not None:
            return result
          return response
      return wraps(view_func)(_wrapped_view)
    return auto_adapt_to_methods(_decorator)
  return _make_decorator


def retry_on_timeout(retries=3, secs=1):
  """A decorator to retry a given function performing db operations."""
  import time
  import logging
  from google.appengine.ext import db
  def _decorator(func):
    def _wrapper(*args, **kwds):
      tries = 0
      while True:
        try:
          tries += 1
          return func(*args, **kwds)
        except db.Timeout, e:
          logging.debug(e)
          if tries > retries:
            raise e
          else:
            wait_secs = secs * tries ** 2
            logging.warning("Retrying function %r in %d secs" %
                            (func, wait_secs))
            time.sleep(wait_secs)
    return _wrapper
  return _decorator

def cron_only(func):
  from werkzeug.exceptions import Forbidden
  def inner(request, *args, **kwargs):
    from kay.utils import is_dev_server
    from kay.conf import settings

    # Only allow access in the following cases
    # 1. We are using the dev server in DEBUG mode
    # 2. The X-AppEngine-Cron request header is set to true
    if (not (is_dev_server() and settings.DEBUG) and
        not request.headers.get("X-AppEngine-Cron") == "true"):
      raise Forbidden("This URL is cron only")
    return func(request, *args, **kwargs)
  return inner

cron_only = auto_adapt_to_methods(cron_only)

def maintenance_check(endpoint='_internal/maintenance_page'):
  """
  checks if datastore capabilities stays available for certain time.
  """
  import logging
  from google.appengine.api.capabilities import CapabilitySet
  from werkzeug import redirect
  from kay.utils import url_for
  from kay.i18n import gettext as _

  arg_exist = True
  if callable(endpoint):
    _endpoint = endpoint
    endpoint = '_internal/maintenance_page'
    arg_exist = False
  def decorator(view):
    def wrapped(request, *args, **kwargs):
      datastore_write = CapabilitySet('datastore_v3', capabilities=['write'])
      datastore_writable = datastore_write.will_remain_enabled_for(60)
      if not datastore_writable:
        logging.warn('Datastore is not writable. %s' %
                     datastore_write.admin_message())
        if not request.is_xhr:
          return redirect(url_for(endpoint))
      return view(request, *args, **kwargs)
    update_wrapper(wrapped, view)
    return wrapped
  if not arg_exist:
    return auto_adapt_to_methods(decorator)(_endpoint)
  return auto_adapt_to_methods(decorator)


class memcache_property(object):
  """A decorator that converts a function into a lazy property.  The
  function wrapped is called the first time to retrieve the result
  and then that calculated result is used the next time you access
  the value. The decorator takes one manditory key factory function
  that takes the owning object as it's only argument and returns
  a key to be used to store in memcached::

      class Foo(db.Model):

        @memcached_property(lambda o: "Foo:%s:foo" % o.key().name())
        def foo(self):
          # calculate something important here
          return 42

  The class has to have a `__dict__` in order for this property to
  work.
  """

  # implementation detail: this property is implemented as non-data
  # descriptor.  non-data descriptors are only invoked if there is
  # no entry with the same name in the instance's __dict__.
  # this allows us to completely get rid of the access function call
  # overhead.  If one choses to invoke __get__ by hand the property
  # will still work as expected because the lookup logic is replicated
  # in __get__ for manual invocation.

  def __init__(self, key_f, expire=0):
    self._key_f = key_f
    self._expire = expire

  def __call__(self, func, name=None, doc=None):
    self.__name__ = name or func.__name__
    self.__module__ = func.__module__
    self.__doc__ = doc or func.__doc__
    self.func = func
    return self

  def __get__(self, obj, type=None):
    if obj is None:
      return self
    value = obj.__dict__.get(self.__name__, _missing)
    if value is _missing:
      memcached_key = self._key_f(obj)
      if memcached_key is not None:
          value = memcache.get(memcached_key)
      if value is _missing or not value:
        value = self.func(obj)
        obj.__dict__[self.__name__] = value
        if memcached_key is not None:
            memcache.set(memcached_key, value, self._expire)
    return value
