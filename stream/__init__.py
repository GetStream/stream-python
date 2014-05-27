
__author__ = 'Thierry Schellenbach'
__copyright__ = 'Copyright 2012, Thierry Schellenbach'
__credits__ = ['Thierry Schellenbach, mellowmorning.com, @tschellenbach']
__license__ = 'BSD'
__version__ = '0.1.0'
__maintainer__ = 'Thierry Schellenbach'
__email__ = 'thierryschellenbach@gmail.com'
__status__ = 'Production'


def connect(api_key, api_secret):
    '''
    Returns a Client object

    :param api_key: your api key
    :param api_secret: the api secret
    '''
    from stream.client import StreamClient
    return StreamClient(api_key, api_secret)


'''
TODO:

pk_gt and pk_gte seems to have the same output (pk_gt doesnt always work)

Test coverage
Pypi entry
Read the docs
Travis setup
'''
