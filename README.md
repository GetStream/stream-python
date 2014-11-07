stream-python
=============

[![image](https://circleci.com/gh/tschellenbach/stream-python.png?circle-token=ca08d1aa53fd4f9c3255a89bde5cb08c59b9586a)](https://circleci.com/gh/tschellenbach/stream-python/tree/master)

[![Coverage Status](https://coveralls.io/repos/tschellenbach/stream-python/badge.png?branch=master)](https://coveralls.io/r/tschellenbach/stream-python?branch=master)

stream-python is a Python client for [Stream](https://getstream.io/).

### Installation

#### Install from Pypi


```bash
pip install stream-python
```

### Usage

```python
# Instantiate a new client
import stream
client = stream.connect('YOUR_API_KEY', 'API_KEY_SECRET')
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
activity_data = {'actor': 1, 'verb': 'run', 'object': 1, 'foreign_id': 'run', '1', 
	'course': {'name': 'Golden Gate park', 'distance': 10},
	'participants': ['Thierry', 'Tommaso'],
	'started_at': datetime.datetime.now()
};
user_feed_1.add_activity(activity_data)

# Remove an activity by its id
user_feed_1.remove("e561de8f-00f1-11e4-b400-0cc47a024be0")
# or by foreign id
user_feed_1.remove(foreign_id='tweet:1')

# Follow another feed
user_feed_1.follow('flat', '42')

# Stop following another feed
user_feed_1.unfollow('flat', '42')

# List followers/following
following = user_feed_1.following(offset=0, limit=2)
followers = user_feed_1.followers(offset=0, limit=10)

# Batch adding activities
activities = [
	{'actor': 1, 'verb': 'tweet', 'object': 1},
	{'actor': 2, 'verb': 'watch', 'object': 3}
]
user_feed_1.add_activities(activities)

# Add an activity and push it to other feeds too using the `to` field
activity = {
    "actor_id":"1",
    "verb":"like",
    "object_id":"3",
    "to":["user:44", "user:45"]
];
user_feed_1.add_activity(activity);

# Generating tokens for client side usage
token = user_feed_1.token
# Javascript client side feed initialization
# user1 = client.feed('user', '1', '{{ token }}');
```

Docs are available on [GetStream.io](http://getstream.io/docs/).

API docs are on [Read the
docs](http://stream-python.readthedocs.org/en/latest/).



### Contributing

First, make sure you can run the test suite. Tests are run via py.test

```bash
py.test stream/tests.py
# with coverage
py.test stream/tests.py --cov stream --cov-report html
# against a local API backend
LOCAL=true py.test stream/tests.py
```
