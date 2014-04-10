# -*- coding: utf-8 -*-

"""
Tools for sending email.

:Copyright: (c) 2009 Accense Technology, Inc. 
                     Takashi Matsuo <tmatsuo@candit.jp>,
                     All rights reserved.
:license: BSD, see LICENSE for more details.
"""

from google.appengine.api import mail

from kay.conf import settings

def mail_admins(subject, message, fail_silently=False):
  """Sends a message to the admins, as defined by the ADMINS setting."""

  sender_mail = settings.DEFAULT_MAIL_FROM
  if sender_mail == 'admin@example.com':
      sender_mail = None

  if not sender_mail and not settings.ADMINS:
    # If neither DEFAULT_MAIL_FROM and ADMINS are set
    # simply do nothing.
    return

  if (settings.DEBUG and not sender_mail and 
          (settings.ADMINS or settings.NOTIFY_ERRORS_TO_GAE_ADMINS)):
    # DEPRECATED 1.1
    # This code is deprecated and will be removed in
    # versions >= 1.5 or 2.0
    import logging
    logging.debug("Deprecation warning. Please set the DEFAULT_MAIL_FROM "
                 "setting in your settings.py. You will need to set the "
                 "DEFAULT_MAIL_FROM setting in order for error mails to "
                 "work properly in future versions of kay.")

  if settings.NOTIFY_ERRORS_TO_GAE_ADMINS:
    mail.send_mail_to_admins(sender=sender_mail or settings.ADMINS[0][1],
                             subject=subject,
                             body=message)

  for admin in settings.ADMINS:
    mail.send_mail(sender=sender_mail or admin[1],
                   to=admin[1],
                   subject=subject,
                   body=message)
