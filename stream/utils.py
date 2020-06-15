import re

valid_re = re.compile(r"^[\w-]+$")


def validate_feed_id(feed_id):
    """
    Validates the input is in the format of user:1

    :param feed_id: a feed such as user:1

    Raises ValueError if the format doesn't match
    """
    feed_id = str(feed_id)
    if len(feed_id.split(":")) != 2:
        msg = "Invalid feed_id spec %s, please specify the feed_id as feed_slug:feed_id"
        raise ValueError(msg % feed_id)

    feed_slug, user_id = feed_id.split(":")
    validate_feed_slug(feed_slug)
    validate_user_id(user_id)
    return feed_id


def validate_feed_slug(feed_slug):
    """
    Validates the feed slug
    """
    feed_slug = str(feed_slug)
    if not valid_re.match(feed_slug):
        msg = "Invalid feed slug %s, please only use letters, numbers and _"
        raise ValueError(msg % feed_slug)
    return feed_slug


def validate_user_id(user_id):
    """
    Validates the user id
    """
    user_id = str(user_id)
    if not valid_re.match(user_id):
        msg = "Invalid user id %s, please only use letters, numbers and _"
        raise ValueError(msg % user_id)
    return user_id


def validate_foreign_id_time(foreign_id_time):
    if not isinstance(foreign_id_time, (list, tuple)):
        raise ValueError("foreign_id_time should be a list of tuples")

    for v in foreign_id_time:
        if not isinstance(v, (list, tuple)):
            raise ValueError("foreign_id_time elements should be lists or tuples")

        if len(v) != 2:
            raise ValueError("foreign_id_time elements should have two elements")


def get_reaction_params(reactions):
    if reactions is not None and not isinstance(reactions, (dict,)):
        raise TypeError("reactions argument should be a dictionary")

    params = {}
    if reactions is not None:
        if reactions.get("own"):
            params["withOwnReactions"] = True
        if reactions.get("recent"):
            params["withRecentReactions"] = True
        if reactions.get("counts"):
            params["withReactionCounts"] = True
        kinds = reactions.get("kinds")
        if kinds:
            if isinstance(kinds, list):
                kinds = ",".join(k.strip() for k in kinds if k.strip())
            params["reactionKindsFilter"] = kinds
    return params
