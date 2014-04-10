# -*- coding: utf-8 -*-

"""
kay.handlers.ereporter

Wrapper handler for the ereporter report generator.

:Copyright: (c) 2011 Ian Lewis <ianmlewis@gmail.com> All rights reserved.
:license: BSD, see LICENSE for more details.
"""

import logging
import datetime
import itertools
import os
import re

from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext import ereporter

from werkzeug import Response

from kay.conf import settings
from kay.handlers import BaseHandler
from kay.utils.decorators import cron_only
from kay.ext.ereporter.models import ExceptionRecord

def isTrue(val):
  """Determines if a textual value represents 'true'.

  Args:
    val: A string, which may be 'true', 'yes', 't', '1' to indicate True.
  Returns:
    True or False
  """
  val = val.lower()
  return val == 'true' or val == 't' or val == '1' or val == 'yes'

def GetQuery(query_date=None, major_version=None,
             minor_version=None, order=None):
  """Creates a query object that will retrieve the appropriate exceptions.

  Returns:
    A query to retrieve the exceptions required.
  """
  q = ExceptionRecord.all()
  if query_date:
      q.filter('date =', query_date)
  if major_version:
      q.filter('major_version =', major_version)
  if minor_version:
    q.filter('minor_version =', minor_version)
  if order:
    q.order(order)
  return q

class ReportGenerator(BaseHandler):
  """Handler class to generate and email an exception report."""

  DEFAULT_MAX_RESULTS = 100

  @cron_only
  def get(self):
    from kay.utils import render_to_string

    version_filter = self.request.args.get('versions', 'all')
    sender = self.request.args.get('sender', settings.DEFAULT_MAIL_FROM)
    to = self.request.args.get('to', None)
    report_date = self.request.args.get('date', None)
    if report_date:
      yesterday = datetime.date(*[int(x) for x in report_date.split('-')])
    else:
      yesterday = datetime.date.today() - datetime.timedelta(days=1)
    app_id = os.environ['APPLICATION_ID']
    version = os.environ['CURRENT_VERSION_ID']
    major_version, minor_version = version.rsplit('.', 1)
    minor_version = int(minor_version)
    max_results = int(self.request.args.get('max_results',
                                                self.DEFAULT_MAX_RESULTS))
    query_args = {
      'query_date': yesterday,
      'major_version': major_version,
    }
    if version_filter.lower() == 'latest':
      query_args['minor_version'] = minor_version

    try:
      exceptions = GetQuery(order='-minor_version', **query_args).fetch(max_results)
    except db.NeedIndexError:
      exceptions = GetQuery(**query_args).fetch(max_results)

    if exceptions:
      # Format the exceptions and generate the report

      exceptions.sort(key=lambda e: (e.minor_version, -e.count))
      versions = [(minor, list(excs)) for minor, excs
                    in itertools.groupby(exceptions, lambda e: e.minor_version)]

      template_values = {
        'version_filter': version_filter,
        'version_count': len(versions),
        'exception_count': sum(len(excs) for _, excs in versions),
        'occurrence_count': sum(y.count for x in versions for y in x[1]),
        'app_id': app_id,
        'major_version': major_version,
        'date': yesterday,
        'versions': versions,
      }
      report = render_to_string('ereporter/report.html', template_values)
      report_text = render_to_string('ereporter/report.txt', template_values)

      if settings.DEBUG:
        return Response(report, mimetype="text/html")
      else:
        # Send the error mail.
        subject = ('Daily exception report for app "%s", major version "%s"'
                   % (app_id, major_version))
        mail_args = {
            'subject': subject,
            'body': report_text,
            'html': report,
        }
        if to:
          mail_args['to'] = to
          mail_args['sender'] = sender
          mail.send_mail(**mail_args)
        else:
          from kay.mail import mail_admins
          mail_admins(**mail_args)

      if isTrue(self.request.args.get('delete', 'true')):
        db.delete(exceptions)

    return Response()

report_generator = ReportGenerator()

def report_admin(request):
  from kay.utils import render_to_response
  from kay.utils.paginator import Paginator

  version_filter = request.args.get('versions', 'all')
  report_date = request.args.get('date', None)
  if report_date:
    yesterday = datetime.date(*[int(x) for x in report_date.split('-')])
  else:
    yesterday = None

  app_id = os.environ['APPLICATION_ID']
  version = os.environ['CURRENT_VERSION_ID']
  major_version, minor_version = version.rsplit('.', 1)
  minor_version = int(minor_version)

  query_args = {
    'major_version': major_version,
  }
  if yesterday:
    query_args['query_date'] = yesterday

  try:
    exceptions = GetQuery(order='-date', **query_args)
    paginator = Paginator(exceptions, 10)
    page = paginator.page(request.args.get('page', 1))
  except db.NeedIndexError, e:
    logging.warn(e)
    exceptions = GetQuery(**query_args)
    paginator = Paginator(exceptions, 10)
    page = paginator.page(request.args.get('page', 1))

  return render_to_response("ereporter/admin.html", {
    'version_filter': version_filter,
    'app_id': app_id,
    'major_version': major_version,
    'exceptions': page.object_list,
    'paginator': paginator,
    'page': page,
  })
