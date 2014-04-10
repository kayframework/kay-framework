# -*- coding: utf-8 -*-

from kay.utils import forms
from kay.utils.forms.modelform import ModelForm
from kay.ext.live_settings.models import KayLiveSetting
from kay.i18n import lazy_gettext as _

class KayLiveSettingForm(ModelForm):
  key_name = forms.TextField()
  value = forms.TextField(widget=forms.TextInput)
  class Meta:
    model = KayLiveSetting
    fields = ('key_name', 'value')

class KayNamespaceForm(forms.Form):
  csrf_protected = False 

  namespace = forms.RegexField("^[0-9A-Za-z._-]*$",
    max_length=100,
    required=False,
    messages={
      'invalid': _("The namespace name can only contain alpha-numeric and '.', '_', '-' characters."),
    }
  )
