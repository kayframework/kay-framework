=========================
Pagination
=========================

.. module:: kay.utils.paginator
   :synopsis: Classes to help you easily manage paginated data.

Kay provides some classes that help manage paginated data. Paginated data is data
that is spread across several pages and is navigated using "Previous" and "Next" links.

These classes are located in the ``kay.utils.paginator`` module.

Example
=========================

.. code-block:: python

    >>> from kay.utils.paginator import Paginator
    >>> object_list = ["spam", "eggs", "googoo", "gaagaa"]
    >>> p = Paginator(object_list, 2)

    >>> p.count
    4
    >>> p.num_pages
    2
    >>> p.page_range
    [1, 2]

    >>> page1 = p.page(1)
    >>> page1
    <Page 1 of 2>

    >>> page1.object_list
    ['spam', 'eggs']

    >>> page2 = p.page(2)
    >>> page2.object_list
    ['googoo', 'gaagaa']
    >>> page2.has_next
    False
    >>> page2.has_previous
    True
    >>> page2.has_other_pages
    True
    >>> page2.next_page_number
    3
    >>> page2.previous_page_number
    1
    >>> page2.start_index
    3
    >>> page2.end_index
    4

    >>> p.page(0)
    Traceback (most recent call last)
    ...
    EmptyPage: That page number is less than 1

    >>> p.page(3)
    Traceback (most recent call last)
    ...
    EmptyPage: That page contains no results


.. note:: 

    Note that you can give Paginator a list/tuple, a Kay QuerySet, or any
    other object with a count() or __len__() method. When determining the
    number of objects contained in the passed object, Paginator will first try
    calling count(), then fallback to using len() if the passed object has no
    count() method. This allows objects such as Kay's QuerySet to use a more
    efficient count() method when available.

Using Paginator in a View
=================================

Here's a slightly more complex example using Paginator in a view to paginate a
datastore query. We give both the view and the accompanying jinja2 template to
show how you can display the results. This example assumes you have a Contacts
model that has already been imported.

The view function looks like this:

.. code-block:: python

    from kay.utils.paginator import Paginator, InvalidPage, EmptyPage
    from kay.utils import render_to_response

    def listing(request):
        contact_list = Contacts.all()
        paginator = Paginator(contact_list, 25) # Show 25 contacts per page

        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.args.get('page', '1'))
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            contacts = paginator.page(page)
        except (EmptyPage, InvalidPage):
            contacts = paginator.page(paginator.num_pages)

        return render_to_response('list.html', {"contacts": contacts})

.. code-block:: html+django

    {% for contact in contacts.object_list %}
    {# Each "contact" is a Contact model object. #}
    {{ contact.full_name|upper }}<br />
    ...
    {% endfor %}

    <div class="pagination">
        <span class="step-links">
            {% if contacts.has_previous %}
                <a href="?page={{ contacts.previous_page_number }}">previous</a>
            {% endif %}

            <span class="current">
                Page {{ contacts.number }} of {{ contacts.paginator.num_pages }}.
            </span>

            {% if contacts.has_next %}
                <a href="?page={{ contacts.next_page_number }}">next</a>
            {% endif %}
        </span>
    </div>

Paginator objects
=============================

Paginator objects have the following constructor.

.. class:: Paginator(object_list, per_page, orphans=0, allow_empty_first_page=True, cache_key=None)

Required arguments
------------------

``object_list``
    A list, tuple, Appengine ``Query``, or other sliceable object with a
    ``count()`` or ``__len__()`` method.

``per_page``
    The maximum number of items to include on a page, not including orphans
    (see the ``orphans`` optional argument below).

Optional arguments
------------------

``orphans``
    The minimum number of items allowed on the last page, defaults to zero.
    Use this when you don't want to have a last page with very few items.
    If the last page would normally have a number of items less than or equal
    to ``orphans``, then those items will be added to the previous page (which
    becomes the last page) instead of leaving the items on a page by
    themselves. For example, with 23 items, ``per_page=10``, and
    ``orphans=3``, there will be two pages; the first page with 10 items and
    the  second (and last) page with 13 items.

``allow_empty_first_page``
    Whether or not the first page is allowed to be empty.  If ``False`` and
    ``object_list`` is  empty, then an ``EmptyPage`` error will be raised.

``cache_key``
    A cache key used for internal caching. If this key is provided, internal values
    such as counts can be cached in memcache. This should be some kind of unique value
    based on a user's session.

Methods
-------

.. method:: Paginator.page(number)

    Returns a :class:`Page` object with the given 1-based index. Raises
    :exc:`InvalidPage` if the given page number doesn't exist.

Attributes
----------

.. attribute:: Paginator.count

    The total number of objects, across all pages.

    .. note::

        When determining the number of objects contained in ``object_list``,
        ``Paginator`` will first try calling ``object_list.count()``. If
        ``object_list`` has no ``count()`` method, then ``Paginator`` will
        fallback to using ``object_list.__len__()``. This allows objects, such
        as Appengine's ``Query``, to use a more efficient ``count()`` method
        when available.

.. attribute:: Paginator.num_pages

    The total number of pages.

.. attribute:: Paginator.page_range

    A 1-based range of page numbers, e.g., ``[1, 2, 3, 4]``.

``InvalidPage`` exceptions
==========================

The ``page()`` method raises ``InvalidPage`` if the requested page is invalid
(i.e., not an integer) or contains no objects. Generally, it's enough to trap
the ``InvalidPage`` exception, but if you'd like more granularity, you can trap
either of the following exceptions:

``PageNotAnInteger``
    Raised when ``page()`` is given a value that isn't an integer.

``EmptyPage``
    Raised when ``page()`` is given a valid value but no objects exist on that
    page.

Both of the exceptions are subclasses of ``InvalidPage``, so you can handle
them both with a simple ``except InvalidPage``.


``Page`` objects
================

.. class:: Page(object_list, number, paginator)

You usually won't construct :class:`Pages <Page>` by hand -- you'll get them
using :meth:`Paginator.page`.


Attributes
----------

.. method:: Page.has_next

    ``True`` if there's a next page.

.. method:: Page.has_previous

    ``True`` if there's a previous page.

.. method:: Page.has_other_pages

    ``True`` if there's a next *or* previous page.

.. method:: Page.next_page_number

    The next page number. Note that this is "dumb" and will return the
    next page number regardless of whether a subsequent page exists.

.. method:: Page.previous_page_number

    The previous page number. Note that this is "dumb" and will return
    the previous page number regardless of whether a previous page exists.

.. method:: Page.start_index

    A 1-based index of the first object on the page, relative to all
    of the objects in the paginator's list. For example, when paginating a list
    of 5 objects with 2 objects per page, the second page's :meth:`~Page.start_index`
    would return ``3``.

.. method:: Page.end_index

    A the 1-based index of the last object on the page, relative to all of
    the objects in the paginator's list. For example, when paginating a list of
    5 objects with 2 objects per page, the second page's :meth:`~Page.end_index`
    would return ``4``.

.. attribute:: Page.object_list

    The list of objects on this page.

.. attribute:: Page.number

    The 1-based page number for this page.

.. attribute:: Page.paginator

    The associated :class:`Paginator` object.
