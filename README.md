stream-python
=============

[![Build Status](https://travis-ci.org/GetStream/stream-python.svg?branch=master)](https://travis-ci.org/GetStream/stream-python) [![codecov](https://codecov.io/gh/GetStream/stream-python/branch/master/graph/badge.svg)](https://codecov.io/gh/GetStream/stream-python) [![PyPI version](https://badge.fury.io/py/stream-python.svg)](http://badge.fury.io/py/stream-python)

[stream-python](https://github.com/GetStream/stream-python) is the official Python client for [Stream](https://getstream.io/), a web service for building scalable newsfeeds and activity streams.

Note there is also a higher level [Django - Stream integration](https://github.com/getstream/stream-django) library which hooks into the Django ORM.

You can sign up for a Stream account at https://getstream.io/get_started.

### Installation

#### Install from Pypi

```bash
pip install stream-python
```

### Full documentation

Documentation for this Python client are available at the [Stream website](https://getstream.io/docs/?language=python) or on [Read the Docs](http://stream-python.readthedocs.org/en/latest/).

### Usage

```python
# Instantiate a new client
import stream
client = stream.connect('YOUR_API_KEY', 'API_KEY_SECRET')

# INstantiate a new client specifying datacenter location
client = stream.connect('YOUR_API_KEY', 'API_KEY_SECRET', location='us-east')
# Find your API keys here https://getstream.io/dashboard/

# Instantiate a feed object
user_feed_1 = client.feed('user', '1')

# Get activities from 5 to 10 (slow pagination)
result = user_feed_1.get(limit=5, offset=5)
# (Recommended & faster) Filter on an id less than the given UUID
result = user_feed_1.get(limit=5, id_lt="e561de8f-00f1-11e4-b400-0cc47a024be0")

# Create a new activity
activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1, 'foreign_id': 'tweet:1'}
activity_response = user_feed_1.add_activity(activity_data)
# Create a bit more complex activity
activity_data = {'actor': 1, 'verb': 'run', 'object': 1, 'foreign_id': 'run:1',
	'course': {'name': 'Golden Gate park', 'distance': 10},
	'participants': ['Thierry', 'Tommaso'],
	'started_at': datetime.datetime.now()
}
user_feed_1.add_activity(activity_data)

# Remove an activity by its id
user_feed_1.remove_activity("e561de8f-00f1-11e4-b400-0cc47a024be0")
# or by foreign id
user_feed_1.remove_activity(foreign_id='tweet:1')

# Follow another feed
user_feed_1.follow('flat', '42')

# Stop following another feed
user_feed_1.unfollow('flat', '42')

# List followers/following
following = user_feed_1.following(offset=0, limit=2)
followers = user_feed_1.followers(offset=0, limit=10)

# Creates many follow relationships in one request
follows = [
    {'source': 'flat:1', 'target': 'user:1'},
    {'source': 'flat:1', 'target': 'user:2'},
    {'source': 'flat:1', 'target': 'user:3'}
]
client.follow_many(follows)

# Batch adding activities
activities = [
	{'actor': 1, 'verb': 'tweet', 'object': 1},
	{'actor': 2, 'verb': 'watch', 'object': 3}
]
user_feed_1.add_activities(activities)

# Add an activity and push it to other feeds too using the `to` field
activity = {
    "actor":"1",
    "verb":"like",
    "object":"3",
    "to":["user:44", "user:45"]
}
user_feed_1.add_activity(activity)

# Retrieve an activity by its ID
client.get_activities(ids=[activity_id])

# Retrieve an activity by the combination of foreign_id and time
client.get_activities(foreign_id_time=[
    (foreign_id, activity_time),
])

# Generating tokens for client side usage (JS client)
token = user_feed_1.token
# Javascript client side feed initialization
# user1 = client.feed('user', '1', '{{ token }}');

# Generate a read-only token for client side usage (JS client)
readonly_token = user_feed_1.get_readonly_token()
# Javascript client side feed initialization
# user1 = client.feed('user', '1', '{{ readonly_token }}');

# Generate a redirect url for the Stream Analytics platform to track
# events/impressions on url clicks
impression = {
    'content_list': ['tweet:1', 'tweet:2', 'tweet:3'],
    'user_data': 'tommaso',
    'location': 'email',
    'feed_id': 'user:global'
}

engagement = {
    'content': 'tweet:2',
    'label': 'click',
    'position': 1,
    'user_data': 'tommaso',
    'location': 'email',
    'feed_id':
    'user:global'
}

events = [impression, engagement]

redirect_url = client.create_redirect_url('http://google.com/', 'user_id', events)
```

[JS client](http://github.com/getstream/stream-js).

### Contributing

First, make sure you can run the test suite. Tests are run via py.test

```bash
py.test
# with coverage
py.test --cov stream --cov-report html
# against a local API backend
LOCAL=true py.test
```

### Copyright and License Information

Copyright (c) 2014-2017 Stream.io Inc, and individual contributors. All rights reserved.

See the file "LICENSE" for information on the history of this software, terms & conditions for usage, and a DISCLAIMER OF ALL WARRANTIES.
