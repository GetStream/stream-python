stream-python
=========

.. image:: https://secure.travis-ci.org/tbarbugli/stream-php.png?branch=master
   :target: http://travis-ci.org/tbarbugli/stream-php


stream-php is a Python client for `Stream <https://getstream.io/>`_.

.. code-block:: python

    # Instantiate a new client
    import stream
    client = stream.connect('YOUR_API_KEY', 'API_KEY_SECRET')

    # Instantiate a feed object
    user_feed_1 = client.feed('user:1')

    # Get activities from 5 to 10
    result = user_feed_1.get(limit=5, offset=5)
    activities = result['activities']
    
    # Create a new activity
    activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
    activity_response = user_feed_1.add_activity(activity_data)

    # Remove an activity by its id
    user_feed_1.remove('12345678910')
    
    # Follow another feed
    user_feed_1.follow('flat:42')

    # Stop following another feed
    user_feed_1.unfollow('flat:42')


Installation
------------

Install from Pypi
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install stream-python
    
    

Contributing
------------

First, make sure you can run the test suite. Tests are run via py.test

::

py.test stream/tests.py


