# -*- coding: utf-8 -*-
"""
live_settings.views
"""

from werkzeug import redirect, url_encode
from werkzeug.contrib.securecookie import SecureCookie

from kay.utils import (
  render_to_response, url_for, to_local_timezone,
  set_cookie, delete_cookie
)

from kay.i18n import lazy_gettext as _
from kay.ext.live_settings import live_settings
from kay.ext.live_settings.models import KayLiveSetting
from kay.ext.live_settings.forms import KayLiveSettingForm, KayNamespaceForm

from kay.conf import settings

def _set_flash_msg(request, message):
  set_cookie('ls_message', 
      SecureCookie({'m':message}, settings.SECRET_KEY).serialize())

def _get_flash_msg(request):
  if 'ls_message' in request.cookies:
    update_message = SecureCookie.unserialize(
      request.cookies['ls_message'],
      settings.SECRET_KEY,
    )
    delete_cookie('ls_message')
    return update_message['m']
  else:
    return None

def admin(request):
  nsform = None
  namespace = ''
  if 'namespace' in request.args:
    nsform = KayNamespaceForm()
    if nsform.validate(request.args):
      namespace = nsform['namespace'] or ''
    nsform = nsform.as_widget()

  object_list = list(KayLiveSetting.all(namespace=namespace))
  forms = dict(
      map(lambda s: (s.key().name(), KayLiveSettingForm(instance=s, initial={
          "key_name": s.key().name(),
          "namespace": namespace,
      })), object_list)
  )

  if (request.method == "POST"):
    key_name = request.form.get('key_name')
    if key_name:
        form = forms.get(key_name, None)
        if not form:
          form = KayLiveSettingForm()
        if form.validate(request.form):
          if 'delete' in request.form:
            _set_flash_msg(request, _("Deleted the setting '%(key)s'" % {
              'key': key_name,
            }))
            live_settings.delete(form['key_name'], namespace=namespace)
            if key_name in forms:
              del forms[key_name]
          else:
            _set_flash_msg(request, _("Updated the setting '%(key)s'" % {
              'key': key_name,
            }))
            forms[key_name] = form
            form.instance = live_settings.set(
              form['key_name'],
              form['value'],
              namespace=namespace,
            )
          return redirect(
            "%s?%s" % (
              url_for('live_settings/admin'),
              url_encode(request.args),
            ),
          )
  new_form = KayLiveSettingForm()
  return render_to_response('live_settings/admin.html', {
      'flash_msg': _get_flash_msg(request),
      'to_local_timezone': to_local_timezone, # ensure we have this function
      'nsform': nsform,
      'namespace': namespace,
      'form_list': map(lambda f: (f.instance, f.as_widget()), forms.values()),
      'new_form': new_form.as_widget(),
  })
