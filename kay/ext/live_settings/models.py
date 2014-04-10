# -*- coding: utf-8 -*-
# live_settings.models

from google.appengine.ext import db

class KayLiveSetting(db.Model):
    # key_name = key
    value = db.TextProperty(indexed=False)
    ttl = db.IntegerProperty(indexed=False)
    utime = db.DateTimeProperty(indexed=False, auto_now=True)
