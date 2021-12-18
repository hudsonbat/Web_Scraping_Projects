# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field
from scrapy.loader.processors import MapCompose


class VrboTutorialItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    owner = Field()
    name = Field()
    price = Field()
    rating = Field()
    title = Field()
    amenities = Field()
    location = Field()
    no_bedrooms = Field()
    no_beds = Field()
    no_bathrooms = Field()
    no_reviews = Field()
    no_guests = Field()
    revs = Field()
    ratings = Field()
    availability = Field()
