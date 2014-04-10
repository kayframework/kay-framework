# -*- coding: utf-8 -*-
import logging

from math import ceil

from kay.utils.decorators import memcache_property
from werkzeug.utils import cached_property

__all__ = (
  'InvalidPage', 'PageNotAnInteger',
  'Paginator', 'Page',
)

class InvalidPage(Exception):
  pass

class PageNotAnInteger(InvalidPage):
  pass

class EmptyPage(InvalidPage):
  pass

class Paginator(object):
  def __init__(self, object_list, per_page, allow_empty_first_page=True, cache_key=None):
    self.object_list = object_list
    self.per_page = per_page
    self.allow_empty_first_page = allow_empty_first_page
    self.cache_key = None

  def validate_number(self, number):
    "Validates the given 1-based page number."
    try:
      number = int(number)
    except ValueError:
      raise PageNotAnInteger('That page number is not an integer')
    if number < 1:
      raise EmptyPage('That page number is less than 1')
    return number

  def page(self, number):
    "Returns a Page object for the given 1-based page number."
    number = self.validate_number(number)
    bottom = (number - 1) * self.per_page
    top = bottom + self.per_page
    
    # Get one more entity than requested to see if 
    # we have one more page
    page_items = list(self.object_list[bottom:top+1])
    if not page_items:
      if number == 1 and self.allow_empty_first_page:
        pass
      else:
        raise EmptyPage('That page contains no results')

    # Check if there is a next page
    has_next = len(page_items) > self.per_page
    return Page(page_items[:self.per_page], number, self, has_next)

  @memcache_property(lambda p: ("kay:utils:paginator:%s:count" % p.cache_key) if p.cache_key else None)
  def count(self):
    "Returns the total number of objects, across all pages."
    try:
      return self.object_list.count()
    except (AttributeError, TypeError):
      # AttributeError if object_list has no count() method.
      # TypeError if object_list.count() requires arguments
      # (i.e. is of type list).
      return len(self.object_list)

  @cached_property
  def num_pages(self):
    "Returns the total number of pages."
    if self.count == 0 and not self.allow_empty_first_page:
      return 0
    else:
      return int(ceil(self.count / float(self.per_page)))

  def _get_page_range(self):
    """
    Returns a 1-based range of pages for iterating through within
    a template for loop.
    """
    return range(1, self.num_pages + 1)
  page_range = property(_get_page_range)

class Page(object):
  def __init__(self, object_list, number, paginator, has_next=False):
    self.object_list = object_list
    self.number = number
    self.paginator = paginator
    self.has_next = has_next

  def __repr__(self):
    return '<Page %s of %s>' % (self.number, self.paginator.num_pages)

  @cached_property
  def has_next(self):
    """
    Checks for one more item than last on this page.
    """
    try:
      next_item = self.paginator.object_list[
          self.number * self.paginator.per_page]
    except IndexError:
      return False
    return True

  @property
  def has_previous(self):
    return self.number > 1

  @property
  def has_other_pages(self):
    return self.has_previous or self.has_next

  @property
  def next_page_number(self):
    return self.number + 1

  @property
  def previous_page_number(self):
    return self.number - 1

  @property
  def start_index(self):
    """
    Returns the 1-based index of the first object on this page,
    relative to total objects in the paginator.
    """
    # Special case, return zero if no items.
    if self.number == 1 and len(self.object_list) == 0:
        return 0
    else:
        return (self.paginator.per_page * (self.number - 1)) + 1

  @property
  def end_index(self):
    """
    Returns the 1-based index of the last object on this page,
    relative to total objects found (hits).
    """
    object_num = len(self.object_list)
    if object_num >= self.paginator.per_page:
      return self.number * self.paginator.per_page
    else:
      return ((self.number - 1) * self.paginator.per_page) + object_num
