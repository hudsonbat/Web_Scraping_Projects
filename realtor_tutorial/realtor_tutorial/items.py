# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field
from scrapy.loader.processors import MapCompose,TakeFirst


class RealtorTutorialItem(scrapy.Item):
    taxes = Field()
    prop_hist = Field()
    interior_features = Field()
    appliances = Field(output_processor=TakeFirst())
    heating_cooling = Field(output_processor=TakeFirst())
    garage_info = Field(output_processor=TakeFirst())
    waterfront_access = Field(output_processor=TakeFirst())
    homeowners = Field(output_processor=TakeFirst())
    price = Field()
    link = Field()
    status = Field()
    amenities = Field()
    beds = Field()
    garages = Field()
    stories = Field()
    types = Field()
    baths_full = Field()
    baths_half = Field()
    lot_sqft = Field()
    sqft = Field()
    year_built = Field()
    sold_price = Field()
    sold_date = Field()
    locations = Field()
    list_dates = Field()

