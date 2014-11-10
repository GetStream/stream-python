

def validate_feed(feed_id):
    '''
    Validates the input is in the format of user:1

    :param feed_id: a feed such as user:1

    Raises ValueError if the format doesnt match
    '''
    if len(feed_id.split(':')) != 2:
        msg = 'Invalid feed_id spec %s, please specify the feed_id as feed_slug:feed_id'
        raise ValueError(msg % feed_id)
