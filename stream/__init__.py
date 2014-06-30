import re

__author__ = 'Thierry Schellenbach'
__copyright__ = 'Copyright 2012, Thierry Schellenbach'
__credits__ = ['Thierry Schellenbach, mellowmorning.com, @tschellenbach']
__license__ = 'BSD'
__version__ = '0.2.2'
__maintainer__ = 'Thierry Schellenbach'
__email__ = 'thierryschellenbach@gmail.com'
__status__ = 'Production'


def connect(api_key, api_secret=None, site_id=None):
    '''
    Returns a Client object

    :param api_key: your api key or heroku url
    :param api_secret: the api secret
    :param site_id: the site id (used for listening to feed changes)
    '''
    from stream.client import StreamClient
    
    # support for the heroku STREAM_URL syntax
    if api_key.startswith('https'):
        pattern = re.compile('https\:\/\/(\w+)\:(\w+).*site=(\d+)', re.IGNORECASE)
        result = pattern.match(api_key)
        if result and len(result.groups())==3:
            api_key, api_secret, site_id = result.groups()
        else:
            raise ValueError('Invalid api key or heroku url')
    
    return StreamClient(api_key, api_secret, site_id)


