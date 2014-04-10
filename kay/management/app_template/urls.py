# -*- coding: utf-8 -*-
# %app_name%.urls
# 

from kay.routing import (
  ViewGroup, Rule
)

view_groups = [
  ViewGroup(
    Rule('/', endpoint='index', view='%app_name%.views.index'),
  )
]

