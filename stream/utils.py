

def validate_feed(feed):
    if len(feed.split(':')) != 2:
        msg = 'Invalid feed spec %s, please specify the feed as feed_slug:feed_id'
        raise ValueError(msg % feed)
