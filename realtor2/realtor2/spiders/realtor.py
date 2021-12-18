import scrapy
import json
import math
import time
from scrapy.loader import ItemLoader
from ..items import Realtor2Item
from collections import defaultdict


class RealtorSpider(scrapy.Spider):
    name = 'realtor'
    allowed_domains = ['www.realtor.com']
    start_urls = ['https://www.realtor.com/']
    # handle_httpstatus_list = [403]
    city_states = [
        ('Ocean-City', 'MD'),
        ('Dewey-Beach', 'DE'),
        ('Bethany-Beach', 'DE'),
        ('Rehoboth-Beach', 'DE'),
    ]
    # current_page = 1
    # url = ''
    # pages = 1
    # first = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = ''
        self.pages = 1
        self.first = True

    def start_requests(self):
        for item in self.city_states:
            self.url = f'{self.start_urls[0]}realestateandhomes-search/{item[0]}_{item[1]}'
            self.pages = 1
            self.first = True
            yield scrapy.Request(url=self.url, callback=self.parse)

    def parse(self, response, **kwargs):
        page_data = response.xpath("//script[@id='__NEXT_DATA__']/text()").get()
        jsn = json.loads(page_data)
        new_url=''
        if self.first:
            self.pages = math.ceil(jsn['props']['pageProps']['searchResults']['home_search']['total']/
                        jsn['props']['pageProps']['searchResults']['home_search']['count'])
            self.first = False

        count = len(jsn['props']['pageProps']['searchResults']['home_search']['results'])

        for i in range(count):
            loader = ItemLoader(item=Realtor2Item())
            price = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['list_price']
            link = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['permalink']
            status = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['status']
            beds = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['beds']
            baths_full = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['baths_full']
            baths_half = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['baths_half']
            garages = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['garage']
            stories = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['stories']
            types = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['type']
            lot_sqft = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['lot_sqft']
            sqft = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['sqft']
            year_built = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['year_built']
            sold_price = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['sold_price']
            sold_date = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['description']['sold_date']
            locations = (jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['location']['address']['coordinate']['lat'],
                                          jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['location']['address']['coordinate']['lon'])
            list_dates = jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['list_date']
            try:
                amenities = [item for item in jsn['props']['pageProps']['searchResults']['home_search']['results'][i]['tags']]
            except:
                amenities = 'NA'

            if price:
                loader.add_value('price', price)
            else:
                loader.add_value('price', 'NA')
            if link:
                loader.add_value('link', link)
            else:
                loader.add_value('link', 'NA')
            if status:
                loader.add_value('status', status)
            else:
                loader.add_value('status', 'NA')
            if beds:
                loader.add_value('beds', beds)
            else:
                loader.add_value('beds', 'NA')
            if baths_full:
                loader.add_value('baths_full', baths_full)
            else:
                loader.add_value('baths_full', 'NA')
            if baths_half:
                loader.add_value('baths_half', baths_half)
            else:
                loader.add_value('baths_half', 'NA')
            if garages:
                loader.add_value('garages', garages)
            else:
                loader.add_value('garages', 'NA')
            if stories:
                loader.add_value('stories', stories)
            else:
                loader.add_value('stories', 'NA')
            if types:
                loader.add_value('types', types)
            else:
                loader.add_value('types', 'NA')
            if lot_sqft:
                loader.add_value('lot_sqft', lot_sqft)
            else:
                loader.add_value('lot_sqft', 'NA')
            if sqft:
                loader.add_value('sqft', sqft)
            else:
                loader.add_value('sqft', 'NA')
            if year_built:
                loader.add_value('year_built', year_built)
            else:
                loader.add_value('year_built', 'NA')
            if sold_price:
                loader.add_value('sold_price', sold_price)
            else:
                loader.add_value('sold_price', 'NA')
            if sold_date:
                loader.add_value('sold_date', sold_date)
            else:
                loader.add_value('sold_date', 'NA')
            if locations:
                loader.add_value('locations', locations)
            else:
                loader.add_value('locations', 'NA')
            if list_dates:
                loader.add_value('list_dates', list_dates)
            else:
                loader.add_value('list_dates', 'NA')
            if amenities:
                loader.add_value('amenities', amenities)
            else:
                loader.add_value('amenities', 'NA')

            listing_item = loader.load_item()

            try:
                yield scrapy.Request(f'https://www.realtor.com/realestateandhomes-detail/{link}',
                    callback=self.parse_listing, meta={'listing_item': listing_item})
            except:
                continue

        for i in range(2, self.pages + 1):
            time.sleep(3)
            new_url = self.url
            new_url += f'/pg-{i}'
            self.current_page = i
            yield scrapy.Request(url=new_url, callback=self.parse)

    def parse_listing(self,response):
        listing = response.css('script#__NEXT_DATA__::text').get()
        detail_page = json.loads(listing)
        listing_item = response.meta['listing_item']
        loader = ItemLoader(item=listing_item, response=response)
        category_values = defaultdict(list)

        details = detail_page['props']['pageProps']['property']['details'] or []

        for attribute in details:
            category = attribute['category']
            category_values[category].extend(attribute['text'])

        taxes = detail_page['props']['pageProps']['property']['tax_history'] or []
        prop_hist = detail_page['props']['pageProps']['property']['property_history'] or []

        loader.add_value('taxes', taxes)
        loader.add_value('prop_hist', prop_hist)
        loader.add_value('interior_features', category_values['Interior Features'])
        loader.add_value('appliances', category_values['Appliances'])
        loader.add_value('heating_cooling', category_values['Heating and Cooling'])
        loader.add_value('garage_info', category_values['Garage and Parking'])
        loader.add_value('waterfront_access', category_values['Waterfront and Water Access'])
        loader.add_value('homeowners', category_values['Homeowners Association'])

        yield loader.load_item()

