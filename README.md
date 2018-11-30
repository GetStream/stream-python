stream-python
=============

[![Build Status](https://travis-ci.org/GetStream/stream-python.svg?branch=master)](https://travis-ci.org/GetStream/stream-python) [![codecov](https://codecov.io/gh/GetStream/stream-python/branch/master/graph/badge.svg)](https://codecov.io/gh/GetStream/stream-python) [![PyPI version](https://badge.fury.io/py/stream-python.svg)](http://badge.fury.io/py/stream-python)

[stream-python](https://github.com/GetStream/stream-python) is the official Python client for [Stream](https://getstream.io/), a web service for building scalable newsfeeds and activity streams.

Note there is also a higher level [Django - Stream integration](https://github.com/getstream/stream-django) library which hooks into the Django ORM.

You can sign up for a Stream account at https://getstream.io/get_started.

### Installation

stream-python supports:

- Python (2.6, 2.7, 3.4, 3.5, 3.6, 3.7)

#### Install from Pypi

```bash
pip install stream-python
```

### Full documentation

Documentation for this Python client are available at the [Stream website](https://getstream.io/docs/?language=python) or on [Read the Docs](http://stream-python.readthedocs.org/en/latest/).

### Usage

```python
import datetime

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
client.get_activities(foreign_id_times=[
    (foreign_id, activity_time),
])

# Update some parts of an activity with activity_partial_update
set = {
    'product.name': 'boots',
    'colors': {
        'red': '0xFF0000',
        'green': '0x00FF00'
    }
}
unset = [ 'popularity', 'details.info' ]
# ...by ID
client.activity_partial_update(id=activity_id, set=set, unset=unset)
# ...or by combination of foreign_id and time
client.activity_partial_update(foreign_id=foreign_id, time=activity_time, set=set, unset=unset)

# Generating user token for client side usage (JS client)
user_token = client.create_user_token("user-42")

# Javascript client side feed initialization
# client = stream.connect(apiKey, userToken, appId);

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

Install black and flake8

```
pip install black
pip install flake8
```

Install git hooks to avoid pushing invalid code (git commit will run black and flak8)

### Releasing a new version

In order to release new version you need to be a maintainer on Pypi.

- Update CHANGELOG
- Update the version on setup.py
- Commit and push to Github
- Create a new tag for the version (eg. `v2.9.0`)
- Create a new dist with python `python setup.py sdist`
- Upload the new distributable with wine `twine upload dist/stream-python-VERSION-NAME.tar.gz`

If unsure you can also test using the Pypi test servers `twine upload --repository-url https://test.pypi.org/legacy/ dist/stream-python-VERSION-NAME.tar.gz`

### Copyright and License Information

Copyright (c) 2014-2017 Stream.io Inc, and individual contributors. All rights reserved.

See the file "LICENSE" for information on the history of this software, terms & conditions for usage, and a DISCLAIMER OF ALL WARRANTIES.
