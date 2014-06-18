stream-python
=========

.. image:: https://circleci.com/gh/tschellenbach/stream-python.png?circle-token=ca08d1aa53fd4f9c3255a89bde5cb08c59b9586a
   :target: https://circleci.com/gh/tschellenbach/stream-python/tree/master


.. image:: https://coveralls.io/repos/tschellenbach/stream-python/badge.png
  :target: https://coveralls.io/r/tschellenbach/stream-python


stream-python is a Python client for `Stream <https://getstream.io/>`_.

.. code-block:: python

    # Instantiate a new client
    import stream
    client = stream.connect('YOUR_API_KEY', 'API_KEY_SECRET')
    # Find your API keys here https://getstream.io/dashboard/

    # Instantiate a feed object
    user_feed_1 = client.feed('user:1')

    # Get activities from 5 to 10 (slow pagination)
    result = user_feed_1.get(limit=5, offset=5)
    # (Recommended & faster) Filter on an id less than 112334
    result = user_feed_1.get(limit=5, id_lt=112334)
    
    # Create a new activity
    activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
    activity_response = user_feed_1.add_activity(activity_data)

    # Remove an activity by its id
    user_feed_1.remove('12345678910')
    
    # Follow another feed
    user_feed_1.follow('flat:42')

    # Stop following another feed
    user_feed_1.unfollow('flat:42')
    
    
Docs are available on `GetStream.io`_.

.. _GetStream.io: http://getstream.io/docs/


API docs are on `Read the docs`_.

.. _Read the docs: http://stream-python.readthedocs.org/en/latest/


Installation
------------

Install from Pypi
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install stream-python
    
    

Contributing
------------

First, make sure you can run the test suite. Tests are run via py.test

.. code-block:: bash

    py.test stream/tests.py
    # with coverage
    py.test stream/tests.py --cov stream --cov-report html
    # against a local API backend
    LOCAL=true py.test stream/tests.py


