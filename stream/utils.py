

def validate_feed(feed_id):
    if len(feed_id.split(':')) != 2:
        msg = 'Invalid feed_id spec %s, please specify the feed_id as feed_slug:feed_id'
        raise ValueError(msg % feed_id)
