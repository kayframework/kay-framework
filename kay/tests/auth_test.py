
import os

from werkzeug import (
  BaseResponse, Request
)

from kay.utils.test import Client
from kay.utils import url_for
from kay.app import get_application
from kay.conf import LazySettings
from kay.ext.testutils.gae_test_base import GAETestBase

class GoogleBackendTestCase(GAETestBase):
  KIND_NAME_UNSWAPPED = False
  USE_PRODUCTION_STUBS = True
  CLEANUP_USED_KIND = True
  
  def setUp(self):
    try:
      self.original_user = os.environ['USER_EMAIL']
      self.original_is_admin = os.environ['USER_IS_ADMIN']
      del os.environ['USER_EMAIL']
      del os.environ['USER_IS_ADMIN']
    except Exception:
      pass
    s = LazySettings(settings_module='kay.tests.google_settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)
    self.client.test_logout()

  def tearDown(self):
    self.client.test_logout()

  def test_login(self):
    response = self.client.get(url_for('auth_testapp/index'))
    self.assertEqual(response.status_code, 200)
    response = self.client.get(url_for('auth_testapp/secret'))
    self.assertEqual(response.status_code, 302)
    response = self.client.get(url_for('auth_testapp/c_secret'))
    self.assertEqual(response.status_code, 302)
    self.client.test_login(email="test@example.com", is_admin="1")
    response = self.client.get(url_for('auth_testapp/secret'))
    self.assertEqual(response.status_code, 200)
    response = self.client.get(url_for('auth_testapp/c_secret'))
    self.assertEqual(response.status_code, 200)
    self.client.test_logout()
    response = self.client.get(url_for('auth_testapp/secret'))
    self.assertEqual(response.status_code, 302)
    response = self.client.get(url_for('auth_testapp/c_secret'))
    self.assertEqual(response.status_code, 302)

class DatastoreBackendTestCase(GAETestBase):
  KIND_NAME_UNSWAPPED = False
  USE_PRODUCTION_STUBS = True
  CLEANUP_USED_KIND = True
  
  def setUp(self):
    s = LazySettings(settings_module='kay.tests.datastore_settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)

  def tearDown(self):
    self.client.test_logout()

  def test_login(self):
    from kay.auth import create_new_user
    create_new_user("foobar", "password", is_admin=False)
    response = self.client.get(url_for('auth_testapp/index'))
    self.assertEqual(response.status_code, 200)
    response = self.client.get(url_for('auth_testapp/secret'))
    self.assertEqual(response.status_code, 302)
    self.assert_(response.headers.get('Location').endswith(
        '/auth/login?next=http%253A%252F%252Flocalhost%252Fsecret'))

    self.client.test_login(username='foobar')
    response = self.client.get(url_for('auth_testapp/secret'))
    self.assertEqual(response.status_code, 200)
    self.client.test_logout()
    response = self.client.get(url_for('auth_testapp/secret'))
    self.assertEqual(response.status_code, 302)

  def test_create_inactive_user(self):
      from kay.auth.models import DatastoreUser
      from kay.utils import crypto

      user = DatastoreUser.create_inactive_user("testuser", "password",
                                                "testuser@example.com",
                                                do_registration=False) 
      self.assertEqual(user.key().name(),
                       DatastoreUser.get_key_name("testuser"))
      self.assertEqual(user.user_name, "testuser")
    
      self.assertTrue(crypto.check_pwhash(user.password, "password"))
      self.assertEqual(user.email, "testuser@example.com")

class GAEMABackendTestCase(GAETestBase):
  KIND_NAME_UNSWAPPED = False
  USE_PRODUCTION_STUBS = True
  CLEANUP_USED_KIND = True

  def setUp(self):
    s = LazySettings(settings_module='kay.tests.gaema_settings')
    app = get_application(settings=s)
    self.client = Client(app, BaseResponse)

  def tearDown(self):
    self.client.test_logout(service='shehas.net')

  def test_login(self):
    response = self.client.get(url_for('gaema_testapp/index'))
    self.assertEqual(response.status_code, 200)
    response = self.client.get(url_for('gaema_testapp/secret',
                                       domain_name='shehas.net'))
    self.assertEqual(response.status_code, 302)
    self.assert_(response.headers.get('Location').endswith(
        '/_ah/gaema/marketplace_login/a/shehas.net'))

    self.client.test_login(service='shehas.net',
                           user_data={'claimed_id': 'http://shehas.net/123',
                                      'email': 'tmatsuo@shehas.net'})

    response = self.client.get(url_for('gaema_testapp/secret',
                                       domain_name='shehas.net'))
    self.assertEqual(response.status_code, 200)

    response = self.client.get(url_for('gaema_testapp/secret',
                                       domain_name='example.com'))
    self.assertEqual(response.status_code, 302)
    self.assert_(response.headers.get('Location').endswith(
        '/_ah/gaema/marketplace_login/a/example.com'))

    self.client.test_logout(service='shehas.net')

    response = self.client.get(url_for('gaema_testapp/secret',
                                       domain_name='shehas.net'))
    self.assertEqual(response.status_code, 302)
    
