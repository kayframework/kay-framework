# -*- coding: utf-8 -*-


from werkzeug import (
  BaseResponse, Client, Request
)
from google.appengine.ext.appstats import recording

from kay.app import get_application
from kay.conf import LazySettings
from kay.ext.testutils.gae_test_base import GAETestBase
from kay.ext.live_settings import live_settings
from kay.ext.live_settings.models import KayLiveSetting


class LiveSettingsTestCase(GAETestBase):
  def setUp(self):
    from google.appengine.api import memcache
    memcache.flush_all()
    s = LazySettings(settings_module='kay.tests.live_settings_settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)

    live_settings.set("setting.1", "on")
    live_settings.set("setting.2", "off")

  def test_set(self):
    value = live_settings.set("test.value", "on", expire=120)
    self.assertEqual(value.value, "on")
    self.assertEqual(value.ttl, 120)

  def test_get(self):
    value = live_settings.get("setting.1", "default")
    self.assertEqual(value, "on")
    value = live_settings.get("setting.3", "default")
    self.assertEqual(value, "default")

  def test_get_multi(self):
    value = live_settings.get_multi(["setting.1", "setting.2", "setting.3"])
    self.assertEqual(value, {
        'setting.1': 'on',
        'setting.2': 'off',
        'setting.3': None,
    })

  def test_set_multi(self):
    live_settings.set_multi({
        'setting.1': 'off',
        'setting.a': 'on',
        'setting.b': 'off',
        'setting.c': u'日本語',
    })

    self.assertEqual(live_settings.get('setting.1'), 'off')
    self.assertEqual(live_settings.get('setting.a'), 'on')
    self.assertEqual(live_settings.get('setting.b'), 'off')
    self.assertEqual(live_settings.get('setting.c'), u'日本語')

  def test_delete(self):
    value = live_settings.get("setting.1", "default")
    self.assertEqual(value, "on")
    live_settings.delete('setting.1')
    value = live_settings.get("setting.1", "default")
    self.assertEqual(value, 'default')

  def test_keys(self):
    keys = live_settings.keys()
    self.assertEqual(keys, ['setting.1','setting.2'])

    value = live_settings.set("test.value", "on", expire=120)
    keys = live_settings.keys()
    self.assertEqual(keys, ['setting.1','setting.2', 'test.value'])

  def test_items(self):
    items = live_settings.items()
    self.assertTrue(('setting.1', 'on') in items)
    self.assertTrue(('setting.2', 'off') in items)

    live_settings.set("test.value", "on", expire=120)
    items = live_settings.items()
    test_items = [('setting.1', 'on'), ('setting.2', 'off'), ('test.value', 'on')]
    for item in test_items:
      self.assertTrue(item in items)
