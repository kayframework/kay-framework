# -*- coding: utf-8 -*-

"""
Kay framework.

:Copyright: (c) 2009 Accense Technology, Inc. 
                     Takashi Matsuo <tmatsuo@candit.jp>,
                     Ian Lewis <IanMLewis@gmail.com>
                     All rights reserved.
:license: BSD, see LICENSE for more details.
"""

import os
import sys
import logging

import settings

__version__ = "3.0.0"
__version_info__ = (3, 0, 0, 'final', 0)

KAY_DIR = os.path.abspath(os.path.dirname(__file__))
LIB_DIR = os.path.join(KAY_DIR, 'lib')
PROJECT_DIR = os.path.abspath(os.path.dirname(settings.__file__))
PROJECT_LIB_DIR = os.path.join(PROJECT_DIR, 'lib')

def setup_env(manage_py_env=False):
  """Configures app engine environment for command-line apps."""
  # Try to import the appengine code from the system path.
  try:
    from google.appengine.api import apiproxy_stub_map
  except ImportError, e:
    # Not on the system path. Build a list of alternative paths where it
    # may be. First look within the project for a local copy, then look for
    # where the Mac OS SDK installs it.
    paths = [os.path.join(PROJECT_DIR, '.google_appengine'),
             '/usr/local/google_appengine']
    for path in os.environ.get('PATH', '').replace(';', ':').split(':'):
      path = path.rstrip(os.sep)
      if path.endswith('google_appengine'):
        paths.append(path)
    if os.name in ('nt', 'dos'):
      prefix = '%(PROGRAMFILES)s' % os.environ
      paths.append(prefix + r'\Google\google_appengine')
    # Loop through all possible paths and look for the SDK dir.
    SDK_PATH = None
    for sdk_path in paths:
      sdk_path = os.path.realpath(sdk_path)
      if os.path.exists(sdk_path):
        SDK_PATH = sdk_path
        break
    if SDK_PATH is None:
      # The SDK could not be found in any known location.
      sys.stderr.write('The Google App Engine SDK could not be found!\n'
                       'Please visit http://kay-docs.shehas.net/'
                       ' for installation instructions.\n')
      sys.exit(1)
    # Add the SDK and the libraries within it to the system path.
    SDK_PATH = os.path.realpath(SDK_PATH)
    # if SDK_PATH points to a file, it could be a zip file.
    if os.path.isfile(SDK_PATH):
      import zipfile
      gae_zip = zipfile.ZipFile(SDK_PATH)
      lib_prefix = os.path.join('google_appengine', 'lib')
      lib = os.path.join(SDK_PATH, lib_prefix)
      pkg_names = []
      # add all packages archived under lib in SDK_PATH zip.
      for filename in sorted(e.filename for e in gae_zip.filelist):
        # package should have __init__.py
        if (filename.startswith(lib_prefix) and
            filename.endswith('__init__.py')):
          pkg_path = filename.replace(os.sep+'__init__.py', '')
          # True package root should have __init__.py in upper directory,
          # thus we can treat only the shortest unique path as package root.
          for pkg_name in pkg_names:
            if pkg_path.startswith(pkg_name):
              break
          else:
            pkg_names.append(pkg_path)
      # insert populated EXTRA_PATHS into sys.path.
      EXTRA_PATHS = ([os.path.dirname(os.path.join(SDK_PATH, pkg_name))
                      for pkg_name in pkg_names]
                     + [os.path.join(SDK_PATH, 'google_appengine')])
      sys.path = EXTRA_PATHS + sys.path
      # tweak dev_appserver so to make zipimport and templates work well.
      from google.appengine.tools import dev_appserver
      # make GAE SDK to grant opening library zip.
      dev_appserver.FakeFile.ALLOWED_FILES.add(SDK_PATH)
      template_dir = 'google_appengine/templates/'
      dev_appserver.ApplicationLoggingHandler.InitializeTemplates(
        gae_zip.read(template_dir+dev_appserver.HEADER_TEMPLATE),
        gae_zip.read(template_dir+dev_appserver.SCRIPT_TEMPLATE),
        gae_zip.read(template_dir+dev_appserver.MIDDLE_TEMPLATE),
        gae_zip.read(template_dir+dev_appserver.FOOTER_TEMPLATE))
    # ... else it could be a directory.
    else:
      sys.path = [SDK_PATH] + sys.path
      from appcfg import EXTRA_PATHS as appcfg_EXTRA_PATHS
      from appcfg import GOOGLE_SQL_EXTRA_PATHS as appcfg_SQL_EXTRA_PATHS
      sys.path = sys.path + appcfg_EXTRA_PATHS + appcfg_SQL_EXTRA_PATHS

    # corresponds with another google package
    if sys.modules.has_key('google'):
      del sys.modules['google']
    from google.appengine.api import apiproxy_stub_map
  setup()

  if not manage_py_env:
    return
  print 'Running on Kay-%s' % __version__

def setup():
  setup_syspath()

def setup_syspath():
  if not PROJECT_DIR in sys.path:
    sys.path = [PROJECT_DIR] + sys.path
  if not LIB_DIR in sys.path:
    sys.path = [LIB_DIR] + sys.path
  if not PROJECT_LIB_DIR in sys.path:
    sys.path = [PROJECT_LIB_DIR] + sys.path
