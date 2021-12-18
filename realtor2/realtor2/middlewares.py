import base64
from random import choice

from scrapy.http.request import Request

from .user_agents import UA


class ProxyMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.user = settings.get('SMARTPROXY_USER')
        self.password = settings.get('SMARTPROXY_PASSWORD')
        self.endpoint = settings.get('SMARTPROXY_ENDPOINT')
        self.port = settings.get('SMARTPROXY_PORT')

    def process_request(self, request, spider):
        if request.meta.get('dont_proxy'):
            return
        user_credentials = '{user}:{passw}'.format(user=self.user, passw=self.password)
        basic_authentication = 'Basic ' + base64.b64encode(user_credentials.encode()).decode()
        # here let's determine if we need a rotating or sticky session
        if not request.meta.get('sticky_session'):
            # needed to ensure random proxy per request
            # or else ip will only rotate every X seconds even on rotating service ports
            request.headers['Connection'] = 'close'
        host = 'http://{endpoint}:{port}'.format(endpoint=self.endpoint, port=self.port)
        request.meta['proxy'] = host
        request.headers['Proxy-Authorization'] = basic_authentication


class CompetitorMonitoringHeadersMiddleware:
    DEFAULT_HEADERS = default_headers = {
        "Dnt": "1",
        "Upgrade-Insecure-Requests": "1"
    }

    REFERERS = (
        'www.google.com',
        'www.bing.com',
        'www.duckduckgo.com'
    )

    LANGUAGES = ['no', 'nb', 'nn']

    def process_request(self, request, spider):
        if getattr(spider, 'name', '').startswith('megaflis'):
            request.headers.update({
                **request.headers,
                'content-type': 'application/json',
                'referer': request.url,
                'accept': '*/*',
                'dnt': 1,
                'x-requested-with': 'XMLHttpRequest',
                'x-resolvedynamicdata': True,
                'x-includeappshelldata': True
            })
            return
        # fill in missing headers with default headers
        # can configure headers to be left out from the
        # request meta
        if request.meta.get('exclude_headers'):
            template = {
                k: v
                for k, v in self.DEFAULT_HEADERS.items()
                if k not in request.meta['exclude_headers']
            }
        elif request.meta.get('dont_add_headers'):
            template = {}
        else:
            template = self.DEFAULT_HEADERS
        randomized_headers = {
            "user-agent": choice(UA),
            "accept-language": f"{choice(self.LANGUAGES)};q=0.8{choice([', en-GB,en;q=0.7', ', en-US,en;q=0.8'])}",
            "accept-encoding": f"gzip, deflate{choice(['', ', br'])}",
            "accept": choice([
                "*/*",
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
                "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,"
                "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
            ])
        }
        headers = {
            **template,
            **request.headers,
            **{
                key: value
                for key, value in randomized_headers.items()
                if key not in request.meta.get('exclude_headers', [])
            }
        }
        if request.meta.get('add_referer') and not request.url.endswith(('.txt', '.xml', '.gz')):
            headers['referer'] = f'https://{choice(self.REFERERS)}'
        if choice([True, False]):
            headers['Upgrade-Insecure-Requests'] = '1'
        request.headers.update(headers)
        return None

