=============================
Decorators 
=============================

.. module:: kay.utils.decorators

View Decorators
=============================

Kay includes a number of decorators that can be applied to views 
which make development in the appengine environment easier. These
decorators provide support for functionality for views that is
needed often and can be reused.

.. function:: maintenance_check(endpoint='_internal/maintenance_page')

    The ``maintenance_check()`` decorator checks if appengine is in
    maintenance mode and if so redirects the user to a maintenance page.
    By default the maintenance page is at the url routing endpoint
    '_internal/maintenance_page' but this is configurable by providing
    the endpoint argument to the decorator.
    
    ::

        @maintenance_check
        def my_view(request):
            # ...
            return response

.. function:: cron_only()

    The ``cron_only()`` decorator allows you to specify that the view
    should only be accessed by the Appengine cron service. The ``cron_only()``
    decorator checks the appropriate HTTP headers and if the process is
    being accessed by somewhere other than the Appengine cron service then
    a 403 response is returned. However, for development purposes the
    ``cron_only()`` decorator allows one exception. If :attr:`DEBUG` is
    ``True`` and the application is running on the development server
    then the request is allowed.

    ::

        @cron_only
        def my_cron_view(request):
            # ...
            return response

Utility Decorators
=============================

.. function:: retry_on_timeout(retries=3, secs=1)

    The ``retry_on_timeout()`` decorator allows the wrapped function to be
    called multiple times if a datastore API timeout occurs. The wrapped
    function should be `ideponent <http://en.wikipedia.org/wiki/Idempotence>`_.
    This means that the it shouldn't breakthings if the function called
    multiple times.

    ::

        @retry_on_timeout(retries=5)
        def my_writer_func():
            # Some datastore operation
            return

.. function:: auto_adapt_to_methods()

    ``auto_adapt_to_methods()`` is a utility decorator that wraps other
    decorators. It allows decorators to auto adapt to methods to which
    self is passed.
    
    ::

        @auto_adapt_to_methods
        def my_decorator(func):
            def new_func():
                # ...
                return
            return new_func

.. function:: memcache_property(key_f, expire=0)

  A decorator that converts a function into a lazy property. The
  function wrapped is called the first time to retrieve the result and
  then that calculated result is used the next time you access the
  value. The decorator takes one manditory key factory function that
  takes the owning object as it's only argument and returns a key to
  be used to store in memcached::

      class Foo(db.Model):

        @memcached_property(lambda o: "Foo:%s:foo" % o.key().name())
        def foo(self):
          # calculate something important here
          return 42

  The class has to have a `__dict__` in order for this property to
  work.
