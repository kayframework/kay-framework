# -*- coding: utf-8 -*-

"""
Settings and configuration for Kay.

Values will be read from the module passed when initialization and
then, kay.conf.global_settings; see the global settings file for a
list of all possible variables.

:Copyright: (c) 2011 Ian Lewis <ianmlewis@gmail.com>,
                     All rights reserved.
:license: BSD, see LICENSE for more details.
"""

import os
import re
import time
import threading

from google.appengine.ext import db
from google.appengine.api import memcache

from google.appengine.api import namespace_manager

_missing = type('MissingType', (), {'__repr__': lambda x: 'missing'})()

_DEFAULT_TTL = 60

class LiveSettings(object):
  """
  The LiveSettings class is managages persistent global settings
  much like those in settings.py but which can be modified without
  re-deploying an application.

  Things like enabling/disabling appstats or other middleware,
  can be done via live settings.

  Live settings are a string key to unicode text property pair.
  Settings are stored using a three-tiered approach first in
  an in-memory datastructure that is local to a single app instance,
  then as keys in memcached, then finally persistently
  in the datastore.
  
  During a set operation, the key is stored first in the
  datastore, then in memcached with no expiration, then finally
  in the in-memory cache local only to that instance.

  During a get operation the value is recieved from the in-memory
  cache, if missing it is subsequently retrieved from memcached or
  the datastore. Each in-memory key has an in-memory TTL
  which will cause the key to expire and for new values to be
  loaded from memcached during a get operation.

  Memcached keys may be evicted so the datastore is necessary to
  fully persist values.
  """

  def __init__(self):
    self._settings_cache = {}
    self.lock = threading.Lock()

  def _set_local_cache(self, key, value, ttl=_DEFAULT_TTL, namespace=None):
    value = (value, int(time.time())+ttl, ttl)

    with self.lock:
      if namespace not in self._settings_cache:
        self._settings_cache[namespace] = {}
      self._settings_cache[namespace][key] = value

  def _get_local_cache(self, key, default=_missing, namespace=None):
    data = self._settings_cache.get(namespace, {}).get(key, None)
    if data:
      value,expire,ttl = data
      if expire < time.time():
        return default
      else:
        return value
    else:
      return default

  def _del_local_cache(self, key, namespace=None):
    if (namespace in self._settings_cache and 
        key in self._settings_cache[namespace]):
      del self._settings_cache[namespace][key]

  def set(self, key, value, expire=_DEFAULT_TTL, namespace=None):
    from kay.ext.live_settings.models import KayLiveSetting
    
    old_namespace = namespace_manager.get_namespace()
    try:
      if namespace is not None:
        namespace_manager.set_namespace(namespace)

      new_setting = KayLiveSetting(
          key_name=key,
          ttl=expire,
          value=value,
      )
      new_setting.put()

      # Set the memcached key to never expire. It only expires
      # if it is evicted from memory. TTLs are handled by the 
      # in-memory cache.
      memcache.set("kay:live:%s" % key, (value, expire))
       
      self._set_local_cache(key, value, ttl=expire, namespace=namespace)
    finally:
      if namespace is not None:
        namespace_manager.set_namespace(old_namespace)

    return new_setting

  def set_multi(self, data, expire=_DEFAULT_TTL, namespace=None):
    from kay.ext.live_settings.models import KayLiveSetting

    old_namespace = namespace_manager.get_namespace()
    try:
      if namespace is not None:
        namespace_manager.set_namespace(namespace)

      data_items = data.items()
      db.put(map(lambda x: KayLiveSetting(key_name=x[0], ttl=expire, value=x[1]),
          data_items))
      memcache.set_multi(dict(map(lambda x: (
          "kay:live:%s" % x[0], (x[1],expire)
      ), data_items)))
  
      for key, value in data_items:
        self._set_local_cache(key, value, ttl=expire, namespace=namespace)
    finally:
      if namespace is not None:
        namespace_manager.set_namespace(old_namespace)

  def get(self, key, default=None, namespace=None):
    from kay.ext.live_settings.models import KayLiveSetting

    old_namespace = namespace_manager.get_namespace()
    try:
      if namespace is not None:
        namespace_manager.set_namespace(namespace)

      set_dictcache = False
      set_memcache = False
  
      value = self._get_local_cache(key, namespace=namespace)
      expire = _missing
      ttl = _missing
  
      if value is _missing:
        set_dictcache = True
        value = memcache.get("kay:live:%s" % key)
        if value:
          value,ttl = value
        else:
          value,ttl = (_missing, _missing)
      if value is _missing:
        set_memcache = True
        entity = KayLiveSetting.get_by_key_name(key)
        if entity:
          value = entity.value or _missing
          ttl = entity.ttl or _missing
  
      if value is _missing:
        return default
      else:
        if ttl is None or ttl is _missing:
          ttl = _DEFAULT_TTL 
        if set_dictcache:
          self._set_local_cache(key, value, ttl=ttl, namespace=namespace)
        if set_memcache:
          memcache.set("kay:live:%s" % key, (value, ttl))
  
        return value
    finally:
      if namespace is not None:
        namespace_manager.set_namespace(old_namespace)

  def get_multi(self, keys, namespace=None):
    # For the time being just do a bunch of gets to ensure
    # we get the same value as the get() method.
    # TODO: Make this more efficient
    return dict(map(lambda k: (k,self.get(k, namespace=namespace)), keys))

  def delete(self, key, namespace=None):
    from kay.ext.live_settings.models import KayLiveSetting

    old_namespace = namespace_manager.get_namespace()
    try:
      if namespace is not None:
        namespace_manager.set_namespace(namespace)

      setting = KayLiveSetting.get_by_key_name(key)
      if setting:
          setting.delete()
      memcache.delete("kay:live:%s" % key)
      self._del_local_cache(key, namespace=namespace)
    finally:
      if namespace is not None:
        namespace_manager.set_namespace(old_namespace)

  def keys(self, namespace=None):
    from kay.ext.live_settings.models import KayLiveSetting
    old_namespace = namespace_manager.get_namespace()
    try:
      if namespace is not None:
        namespace_manager.set_namespace(namespace)
      return map(lambda e: e.key().name(), KayLiveSetting.all())
    finally:
      if namespace is not None:
        namespace_manager.set_namespace(old_namespace)

  def items(self, namespace=None):
    # For the time being just do a multi_get to ensure 
    # we get the same value as the get() method.
    # TODO: Make this more efficient
    return self.get_multi(self.keys(namespace=namespace), namespace=namespace).items()

live_settings = LiveSettings()
