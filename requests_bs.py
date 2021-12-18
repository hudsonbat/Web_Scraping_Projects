import requests
import time
import json
from datetime import datetime
from random import randint

import pandas as pd

from lxml.html import fromstring

headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'}

search_url = 'https://www.vrbo.com/serp/g'

df = pd.DataFrame({
    'City': ['deep creek lake'],
    'State': ['maryland'],
    'Check_In': [None],
    'Check_Out': [None],
    'Num_Guests': [1]
})  # instantiate your dataframe of inputs here
# print(list(df.iterrows())[0])
# create or import your dataframe with the below columns
inputs = [
    {
        'query': f'{"-".join(row["City"].split(" "))}-{"-".join(row["State"].split(" "))}-united-states-of-america',
        'check_in': row['Check_In'],
        'check_out': row['Check_Out'],
        'num_guests': row['Num_Guests']
    }
    for _, row in df.iterrows()
]


def do_query(inpt):
    payload = make_payload(inpt)
    listings_response = requests.post(search_url, json=payload).json()
    page_count = listings_response['data']['results']['pageCount']
    responses = [listings_response]
    errors = []
    if page_count > 1:
        for page in range(2, page_count + 1):
            paginated_payload = make_payload(inpt, page=page)
            time.sleep(2)
            print(f'Getting page {page}')
            try:
                response = requests.post(search_url, json=paginated_payload).json()
                if 'data' not in response:
                    errors.append({
                        **response,
                        'page': page,
                        'query': paginated_payload['variables']['request']['q']
                    })
                else:
                    responses.append(response)
            except Exception as e:
                print(f'Error posting query {e}', e)
    detail_urls = []
    for response in responses:
        try:
            for listing in response['data']['results']['listings']:
                detail_urls.append(f'https://www.vrbo.com/{listing["detailPageUrl"]}')
        except:
            continue

    return detail_urls, errors


def get_property_details(detail_url):
    detail_page = fromstring(requests.get(detail_url).text)
    script = detail_page.xpath('//script[contains(., "window.__INITIAL_STATE__ =")]/text()')[0]
    _, jsn = script.strip().split('\n')[0].strip(';').split('=', 1)
    property_data = json.loads(jsn)
    prop_owner = property_data['listingReducer']['contact']['name']
    prop_name = property_data['listingReducer']['headline']
    price = property_data['listingReducer']['priceSummary']
    title = property_data['listingReducer']['headline']
    try:
        no_guests = property_data['listingReducer']['houseRules']['maxOccupancy']['guests']
    except:
        no_guests = 'NA'
    rating = property_data['reviewsReducer']['averageRating']
    latitude = property_data['listingReducer']['geoCode']['latitude']
    longitude = property_data['listingReducer']['geoCode']['longitude']
    bedrooms = property_data['listingReducer']['spaces']['spacesSummary']['bedroomCountDisplay']
    bathrooms = property_data['listingReducer']['spaces']['spacesSummary']['bathroomCountDisplay']
    beds = property_data['listingReducer']['spaces']['spacesSummary']['bedCountDisplay']
    no_reviews = property_data['reviewsReducer']['reviewCount']
    revs = [property_data['reviewsReducer']['reviews'][i]['body'] for i in range(len(property_data['reviewsReducer']['reviews']))]
    ratings = [property_data['reviewsReducer']['reviews'][i]['rating'] for i in range(len(property_data['reviewsReducer']['reviews']))]
    next_month_avail = property_data['listingReducer']['availabilityCalendar']['availability']['unitAvailabilityConfiguration']['checkInAvailability'][:32]
    amenities = [
        {
            'name': amenity['amenity']['displayName'],
            'availability': amenity['availability']
        }
        for amenity_category in (property_data['listingReducer']['categorizedAmenities'] or [])
        for amenity in (amenity_category.get('contentItems', []) or [])
    ]
    return {
        'owner': prop_owner,
        'name': prop_name,
        'price': price,
        'rating': rating,
        'title': title,
        'amenities': amenities,
        'location': (latitude, longitude),
        'no_bedrooms': bedrooms,
        'no_beds': beds,
        'no_bathrooms': bathrooms,
        'no_reviews': no_reviews,
        'no_guests': no_guests,
        'revs': revs,
        'ratings': ratings,
        'availability': next_month_avail
    }

def make_payload(inpt, page=1):
    if inpt['check_in'] is not None:
        return {
            "operationName": "SearchRequestQuery",
            "variables": {
                "filterCounts": True,
                "request": {
                    "paging": {
                        "page": page,  # change page here when paginating over listings search results
                        "pageSize": 50
                        # you can try this post request and test out this value to see if you can get more per page
                    },
                    "filterVersion": "1",
                    "coreFilters": {
                        "adults": inpt['num_guests'],  # number of adults staying
                        "maxBathrooms": None,
                        "maxBedrooms": None,
                        "maxNightlyPrice": None,
                        "maxTotalPrice": None,
                        "minBathrooms": 0,
                        "minBedrooms": 0,
                        "minNightlyPrice": 0,
                        "minTotalPrice": None,
                        "pets": 0
                    },
                    "dates": {
                        "arrivalDate": inpt['check_in'],  # "2022-01-11",  # input arrival date
                        "departureDate": inpt['check_out']  # "2022-01-13"  # input departure date
                    },
                    "filters": [],
                    # need additional request to suggestions api to get this value for each property
                    "q": inpt['query']
                },
                "optimizedBreadcrumb": False,
                "vrbo_web_global_messaging_banner": True,
                "Vrbo_reco_large_search_destino": False
            },
            "extensions": {
                "isPageLoadSearch": True
            },
            "query": "query SearchRequestQuery($request: SearchResultRequest!, $filterCounts: Boolean!, $optimizedBreadcrumb: Boolean!, $vrbo_web_global_messaging_banner: Boolean!, $Vrbo_reco_large_search_destino: Boolean!) {\n  results: search(request: $request) {\n    ...querySelectionSet\n    ...DestinationBreadcrumbsSearchResult\n    ...DestinationCarouselSearchResult @include(if: $Vrbo_reco_large_search_destino)\n    ...DestinationMessageSearchResult\n    ...FilterCountsSearchRequestResult\n    ...HitCollectionSearchResult\n    ...ADLSearchResult\n    ...MapSearchResult\n    ...ExpandedGroupsSearchResult\n    ...PagerSearchResult\n    ...SearchTermCarouselSearchResult\n    ...InternalToolsSearchResult\n    ...SEOMetaDataParamsSearchResult\n    ...GlobalInlineMessageSearchResult\n    ...GlobalBannerContainerSearchResult @include(if: $vrbo_web_global_messaging_banner)\n    ...FlexibleDatesSearchResult\n    __typename\n  }\n  ...RequestMarkerFragment\n}\n\nfragment querySelectionSet on SearchResult {\n  id\n  typeaheadSuggestion {\n    uuid\n    term\n    name\n    __typename\n  }\n  geography {\n    lbsId\n    gaiaId\n    location {\n      latitude\n      longitude\n      __typename\n    }\n    isGeocoded\n    shouldShowMapCentralPin\n    __typename\n  }\n  propertyRedirectUrl\n  __typename\n}\n\nfragment DestinationBreadcrumbsSearchResult on SearchResult {\n  destination(optimizedBreadcrumb: $optimizedBreadcrumb) {\n    breadcrumbs {\n      name\n      url\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment DestinationCarouselSearchResult on SearchResult {\n  destinationRecommendationResponse(size: 8, target: SERP_LARGE_SEARCH_TERM_DESTINATION) {\n    ...DestinationCarouselRecommendedDestinationResponse\n    __typename\n  }\n  __typename\n}\n\nfragment DestinationCarouselRecommendedDestinationResponse on RecommendedDestinationResponse {\n  clientRequestId\n  recommendedDestinations {\n    searchTermUuid\n    imageHref\n    recommendationModel\n    breadcrumbs {\n      place {\n        name {\n          simple\n          full\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment HitCollectionSearchResult on SearchResult {\n  page\n  pageSize\n  queryUUID\n  percentBooked {\n    currentPercentBooked\n    __typename\n  }\n  listings {\n    ...HitListing\n    __typename\n  }\n  resultCount\n  pinnedListing {\n    headline\n    listing {\n      ...HitListing\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment HitListing on Listing {\n  virtualTourBadge {\n    name\n    id\n    helpText\n    __typename\n  }\n  amenitiesBadges {\n    name\n    id\n    helpText\n    __typename\n  }\n  multiUnitProperty\n  images {\n    altText\n    c6_uri\n    c9_uri\n    mab {\n      banditId\n      payloadId\n      campaignId\n      cached\n      arm {\n        level\n        imageUrl\n        categoryName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  ...HitInfoListing\n  __typename\n}\n\nfragment HitInfoListing on Listing {\n  listingId\n  ...HitInfoDesktopListing\n  ...HitInfoMobileListing\n  ...PriceListing\n  __typename\n}\n\nfragment HitInfoDesktopListing on Listing {\n  detailPageUrl\n  instantBookable\n  minStayRange {\n    minStayHigh\n    minStayLow\n    __typename\n  }\n  listingId\n  rankedBadges(rankingStrategy: SERP) {\n    id\n    helpText\n    name\n    __typename\n  }\n  propertyId\n  propertyMetadata {\n    headline\n    __typename\n  }\n  superlativesBadges: rankedBadges(rankingStrategy: SERP_SUPERLATIVES) {\n    id\n    helpText\n    name\n    __typename\n  }\n  unitMetadata {\n    unitName\n    __typename\n  }\n  webRatingBadges: rankedBadges(rankingStrategy: SRP_WEB_RATING) {\n    id\n    helpText\n    name\n    __typename\n  }\n  ...DetailsListing\n  ...GeoDistanceListing\n  ...PriceListing\n  ...RatingListing\n  ...MultiUnitHitListing\n  __typename\n}\n\nfragment DetailsListing on Listing {\n  bathrooms {\n    full\n    half\n    toiletOnly\n    __typename\n  }\n  bedrooms\n  propertyType\n  sleeps\n  petsAllowed\n  spaces {\n    spacesSummary {\n      area {\n        areaValue\n        __typename\n      }\n      bedCountDisplay\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment GeoDistanceListing on Listing {\n  geoDistance {\n    text\n    relationType\n    __typename\n  }\n  __typename\n}\n\nfragment PriceListing on Listing {\n  priceSummary: priceSummary {\n    priceAccurate\n    ...PriceSummaryTravelerPriceSummary\n    __typename\n  }\n  priceSummarySecondary: priceSummary(summary: \"displayPriceSecondary\") {\n    ...PriceSummaryTravelerPriceSummary\n    __typename\n  }\n  priceLabel: priceSummary(summary: \"priceLabel\") {\n    priceTypeId\n    pricePeriodDescription\n    __typename\n  }\n  prices {\n    ...VrboTravelerPriceSummary\n    __typename\n  }\n  __typename\n}\n\nfragment PriceSummaryTravelerPriceSummary on TravelerPriceSummary {\n  priceTypeId\n  edapEventJson\n  formattedAmount\n  roundedFormattedAmount\n  pricePeriodDescription\n  __typename\n}\n\nfragment VrboTravelerPriceSummary on PriceSummary {\n  perNight {\n    amount\n    formattedAmount\n    roundedFormattedAmount\n    pricePeriodDescription\n    __typename\n  }\n  total {\n    amount\n    formattedAmount\n    roundedFormattedAmount\n    pricePeriodDescription\n    __typename\n  }\n  label\n  mainPrice\n  __typename\n}\n\nfragment RatingListing on Listing {\n  averageRating\n  reviewCount\n  __typename\n}\n\nfragment MultiUnitHitListing on Listing {\n  propertyMetadata {\n    propertyName\n    __typename\n  }\n  propertyType\n  listingId\n  ...MultiUnitDropdownListing\n  ...MultiUnitModalListing\n  __typename\n}\n\nfragment MultiUnitDropdownListing on Listing {\n  ...MultiUnitListWrapperListing\n  __typename\n}\n\nfragment MultiUnitListWrapperListing on Listing {\n  listingNamespace\n  listingNumber\n  __typename\n}\n\nfragment MultiUnitModalListing on Listing {\n  ...MultiUnitListWrapperListing\n  __typename\n}\n\nfragment HitInfoMobileListing on Listing {\n  detailPageUrl\n  instantBookable\n  minStayRange {\n    minStayHigh\n    minStayLow\n    __typename\n  }\n  listingId\n  rankedBadges(rankingStrategy: SERP) {\n    id\n    helpText\n    name\n    __typename\n  }\n  propertyId\n  propertyMetadata {\n    headline\n    __typename\n  }\n  superlativesBadges: rankedBadges(rankingStrategy: SERP_SUPERLATIVES) {\n    id\n    helpText\n    name\n    __typename\n  }\n  unitMetadata {\n    unitName\n    __typename\n  }\n  webRatingBadges: rankedBadges(rankingStrategy: SRP_WEB_RATING) {\n    id\n    helpText\n    name\n    __typename\n  }\n  ...DetailsListing\n  ...GeoDistanceListing\n  ...PriceListing\n  ...RatingListing\n  ...MultiUnitHitListing\n  __typename\n}\n\nfragment ExpandedGroupsSearchResult on SearchResult {\n  expandedGroups {\n    ...ExpandedGroupExpandedGroup\n    __typename\n  }\n  __typename\n}\n\nfragment ExpandedGroupExpandedGroup on ExpandedGroup {\n  listings {\n    ...HitListing\n    ...MapHitListing\n    __typename\n  }\n  mapViewport {\n    neLat\n    neLong\n    swLat\n    swLong\n    __typename\n  }\n  __typename\n}\n\nfragment MapHitListing on Listing {\n  ...HitListing\n  geoCode {\n    latitude\n    longitude\n    __typename\n  }\n  __typename\n}\n\nfragment FilterCountsSearchRequestResult on SearchResult {\n  id\n  resultCount\n  filterGroups {\n    groupInfo {\n      name\n      id\n      __typename\n    }\n    filters {\n      count @include(if: $filterCounts)\n      checked\n      filter {\n        id\n        name\n        refineByQueryArgument\n        description\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment MapSearchResult on SearchResult {\n  mapViewport {\n    neLat\n    neLong\n    swLat\n    swLong\n    __typename\n  }\n  page\n  pageSize\n  listings {\n    ...MapHitListing\n    __typename\n  }\n  pinnedListing {\n    listing {\n      ...MapHitListing\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PagerSearchResult on SearchResult {\n  fromRecord\n  toRecord\n  pageSize\n  pageCount\n  page\n  resultCount\n  __typename\n}\n\nfragment DestinationMessageSearchResult on SearchResult {\n  destinationMessage(assetVersion: 4) {\n    iconTitleText {\n      title\n      message\n      icon\n      messageValueType\n      link {\n        linkText\n        linkHref\n        __typename\n      }\n      __typename\n    }\n    ...DestinationMessageDestinationMessage\n    __typename\n  }\n  __typename\n}\n\nfragment DestinationMessageDestinationMessage on DestinationMessage {\n  iconText {\n    message\n    icon\n    messageValueType\n    __typename\n  }\n  __typename\n}\n\nfragment ADLSearchResult on SearchResult {\n  parsedParams {\n    q\n    coreFilters {\n      adults\n      children\n      pets\n      minBedrooms\n      maxBedrooms\n      minBathrooms\n      maxBathrooms\n      minNightlyPrice\n      maxNightlyPrice\n      minSleeps\n      __typename\n    }\n    dates {\n      arrivalDate\n      departureDate\n      __typename\n    }\n    sort\n    __typename\n  }\n  page\n  pageSize\n  pageCount\n  resultCount\n  fromRecord\n  toRecord\n  pinnedListing {\n    listing {\n      listingId\n      __typename\n    }\n    __typename\n  }\n  listings {\n    listingId\n    __typename\n  }\n  filterGroups {\n    filters {\n      checked\n      filter {\n        groupId\n        id\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  geography {\n    lbsId\n    name\n    description\n    location {\n      latitude\n      longitude\n      __typename\n    }\n    primaryGeoType\n    breadcrumbs {\n      name\n      countryCode\n      location {\n        latitude\n        longitude\n        __typename\n      }\n      primaryGeoType\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RequestMarkerFragment on Query {\n  requestmarker\n  __typename\n}\n\nfragment SearchTermCarouselSearchResult on SearchResult {\n  discoveryXploreFeeds {\n    results {\n      id\n      title\n      items {\n        ... on SearchDiscoveryFeedItem {\n          type\n          imageHref\n          place {\n            uuid\n            name {\n              full\n              simple\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  typeaheadSuggestion {\n    name\n    __typename\n  }\n  __typename\n}\n\nfragment InternalToolsSearchResult on SearchResult {\n  internalTools {\n    searchServiceUrl\n    __typename\n  }\n  __typename\n}\n\nfragment SEOMetaDataParamsSearchResult on SearchResult {\n  page\n  resultCount\n  pageSize\n  geography {\n    name\n    lbsId\n    breadcrumbs {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment GlobalInlineMessageSearchResult on SearchResult {\n  globalMessages {\n    ...GlobalInlineAlertGlobalMessages\n    __typename\n  }\n  __typename\n}\n\nfragment GlobalInlineAlertGlobalMessages on GlobalMessages {\n  alert {\n    action {\n      link {\n        href\n        text {\n          value\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    body {\n      text {\n        value\n        __typename\n      }\n      link {\n        href\n        text {\n          value\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    id\n    severity\n    title {\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment GlobalBannerContainerSearchResult on SearchResult {\n  globalMessages {\n    ...GlobalBannerGlobalMessages\n    __typename\n  }\n  __typename\n}\n\nfragment GlobalBannerGlobalMessages on GlobalMessages {\n  banner {\n    body {\n      text {\n        value\n        __typename\n      }\n      link {\n        href\n        text {\n          value\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    id\n    severity\n    title {\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment FlexibleDatesSearchResult on SearchResult {\n  percentBooked {\n    currentPercentBooked\n    __typename\n  }\n  __typename\n}\n"
        }
    else:
        return {
            "operationName": "SearchRequestQuery",
            "variables": {
                "filterCounts": True,
                "request": {
                    "paging": {
                        "page": page,  # change page here when paginating over listings search results
                        "pageSize": 50
                        # you can try this post request and test out this value to see if you can get more per page
                    },
                    "filterVersion": "1",
                    "coreFilters": {
                        "adults": inpt['num_guests'],  # number of adults staying
                        "maxBathrooms": None,
                        "maxBedrooms": None,
                        "maxNightlyPrice": None,
                        "maxTotalPrice": None,
                        "minBathrooms": 0,
                        "minBedrooms": 0,
                        "minNightlyPrice": 0,
                        "minTotalPrice": None,
                        "pets": 0
                    },
                    "filters": [],
                    # need additional request to suggestions api to get this value for each property
                    "q": inpt['query']
                },
                "optimizedBreadcrumb": False,
                "vrbo_web_global_messaging_banner": True,
                "Vrbo_reco_large_search_destino": False
            },
            "extensions": {
                "isPageLoadSearch": True
            },
            "query": "query SearchRequestQuery($request: SearchResultRequest!, $filterCounts: Boolean!, $optimizedBreadcrumb: Boolean!, $vrbo_web_global_messaging_banner: Boolean!, $Vrbo_reco_large_search_destino: Boolean!) {\n  results: search(request: $request) {\n    ...querySelectionSet\n    ...DestinationBreadcrumbsSearchResult\n    ...DestinationCarouselSearchResult @include(if: $Vrbo_reco_large_search_destino)\n    ...DestinationMessageSearchResult\n    ...FilterCountsSearchRequestResult\n    ...HitCollectionSearchResult\n    ...ADLSearchResult\n    ...MapSearchResult\n    ...ExpandedGroupsSearchResult\n    ...PagerSearchResult\n    ...SearchTermCarouselSearchResult\n    ...InternalToolsSearchResult\n    ...SEOMetaDataParamsSearchResult\n    ...GlobalInlineMessageSearchResult\n    ...GlobalBannerContainerSearchResult @include(if: $vrbo_web_global_messaging_banner)\n    ...FlexibleDatesSearchResult\n    __typename\n  }\n  ...RequestMarkerFragment\n}\n\nfragment querySelectionSet on SearchResult {\n  id\n  typeaheadSuggestion {\n    uuid\n    term\n    name\n    __typename\n  }\n  geography {\n    lbsId\n    gaiaId\n    location {\n      latitude\n      longitude\n      __typename\n    }\n    isGeocoded\n    shouldShowMapCentralPin\n    __typename\n  }\n  propertyRedirectUrl\n  __typename\n}\n\nfragment DestinationBreadcrumbsSearchResult on SearchResult {\n  destination(optimizedBreadcrumb: $optimizedBreadcrumb) {\n    breadcrumbs {\n      name\n      url\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment DestinationCarouselSearchResult on SearchResult {\n  destinationRecommendationResponse(size: 8, target: SERP_LARGE_SEARCH_TERM_DESTINATION) {\n    ...DestinationCarouselRecommendedDestinationResponse\n    __typename\n  }\n  __typename\n}\n\nfragment DestinationCarouselRecommendedDestinationResponse on RecommendedDestinationResponse {\n  clientRequestId\n  recommendedDestinations {\n    searchTermUuid\n    imageHref\n    recommendationModel\n    breadcrumbs {\n      place {\n        name {\n          simple\n          full\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment HitCollectionSearchResult on SearchResult {\n  page\n  pageSize\n  queryUUID\n  percentBooked {\n    currentPercentBooked\n    __typename\n  }\n  listings {\n    ...HitListing\n    __typename\n  }\n  resultCount\n  pinnedListing {\n    headline\n    listing {\n      ...HitListing\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment HitListing on Listing {\n  virtualTourBadge {\n    name\n    id\n    helpText\n    __typename\n  }\n  amenitiesBadges {\n    name\n    id\n    helpText\n    __typename\n  }\n  multiUnitProperty\n  images {\n    altText\n    c6_uri\n    c9_uri\n    mab {\n      banditId\n      payloadId\n      campaignId\n      cached\n      arm {\n        level\n        imageUrl\n        categoryName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  ...HitInfoListing\n  __typename\n}\n\nfragment HitInfoListing on Listing {\n  listingId\n  ...HitInfoDesktopListing\n  ...HitInfoMobileListing\n  ...PriceListing\n  __typename\n}\n\nfragment HitInfoDesktopListing on Listing {\n  detailPageUrl\n  instantBookable\n  minStayRange {\n    minStayHigh\n    minStayLow\n    __typename\n  }\n  listingId\n  rankedBadges(rankingStrategy: SERP) {\n    id\n    helpText\n    name\n    __typename\n  }\n  propertyId\n  propertyMetadata {\n    headline\n    __typename\n  }\n  superlativesBadges: rankedBadges(rankingStrategy: SERP_SUPERLATIVES) {\n    id\n    helpText\n    name\n    __typename\n  }\n  unitMetadata {\n    unitName\n    __typename\n  }\n  webRatingBadges: rankedBadges(rankingStrategy: SRP_WEB_RATING) {\n    id\n    helpText\n    name\n    __typename\n  }\n  ...DetailsListing\n  ...GeoDistanceListing\n  ...PriceListing\n  ...RatingListing\n  ...MultiUnitHitListing\n  __typename\n}\n\nfragment DetailsListing on Listing {\n  bathrooms {\n    full\n    half\n    toiletOnly\n    __typename\n  }\n  bedrooms\n  propertyType\n  sleeps\n  petsAllowed\n  spaces {\n    spacesSummary {\n      area {\n        areaValue\n        __typename\n      }\n      bedCountDisplay\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment GeoDistanceListing on Listing {\n  geoDistance {\n    text\n    relationType\n    __typename\n  }\n  __typename\n}\n\nfragment PriceListing on Listing {\n  priceSummary: priceSummary {\n    priceAccurate\n    ...PriceSummaryTravelerPriceSummary\n    __typename\n  }\n  priceSummarySecondary: priceSummary(summary: \"displayPriceSecondary\") {\n    ...PriceSummaryTravelerPriceSummary\n    __typename\n  }\n  priceLabel: priceSummary(summary: \"priceLabel\") {\n    priceTypeId\n    pricePeriodDescription\n    __typename\n  }\n  prices {\n    ...VrboTravelerPriceSummary\n    __typename\n  }\n  __typename\n}\n\nfragment PriceSummaryTravelerPriceSummary on TravelerPriceSummary {\n  priceTypeId\n  edapEventJson\n  formattedAmount\n  roundedFormattedAmount\n  pricePeriodDescription\n  __typename\n}\n\nfragment VrboTravelerPriceSummary on PriceSummary {\n  perNight {\n    amount\n    formattedAmount\n    roundedFormattedAmount\n    pricePeriodDescription\n    __typename\n  }\n  total {\n    amount\n    formattedAmount\n    roundedFormattedAmount\n    pricePeriodDescription\n    __typename\n  }\n  label\n  mainPrice\n  __typename\n}\n\nfragment RatingListing on Listing {\n  averageRating\n  reviewCount\n  __typename\n}\n\nfragment MultiUnitHitListing on Listing {\n  propertyMetadata {\n    propertyName\n    __typename\n  }\n  propertyType\n  listingId\n  ...MultiUnitDropdownListing\n  ...MultiUnitModalListing\n  __typename\n}\n\nfragment MultiUnitDropdownListing on Listing {\n  ...MultiUnitListWrapperListing\n  __typename\n}\n\nfragment MultiUnitListWrapperListing on Listing {\n  listingNamespace\n  listingNumber\n  __typename\n}\n\nfragment MultiUnitModalListing on Listing {\n  ...MultiUnitListWrapperListing\n  __typename\n}\n\nfragment HitInfoMobileListing on Listing {\n  detailPageUrl\n  instantBookable\n  minStayRange {\n    minStayHigh\n    minStayLow\n    __typename\n  }\n  listingId\n  rankedBadges(rankingStrategy: SERP) {\n    id\n    helpText\n    name\n    __typename\n  }\n  propertyId\n  propertyMetadata {\n    headline\n    __typename\n  }\n  superlativesBadges: rankedBadges(rankingStrategy: SERP_SUPERLATIVES) {\n    id\n    helpText\n    name\n    __typename\n  }\n  unitMetadata {\n    unitName\n    __typename\n  }\n  webRatingBadges: rankedBadges(rankingStrategy: SRP_WEB_RATING) {\n    id\n    helpText\n    name\n    __typename\n  }\n  ...DetailsListing\n  ...GeoDistanceListing\n  ...PriceListing\n  ...RatingListing\n  ...MultiUnitHitListing\n  __typename\n}\n\nfragment ExpandedGroupsSearchResult on SearchResult {\n  expandedGroups {\n    ...ExpandedGroupExpandedGroup\n    __typename\n  }\n  __typename\n}\n\nfragment ExpandedGroupExpandedGroup on ExpandedGroup {\n  listings {\n    ...HitListing\n    ...MapHitListing\n    __typename\n  }\n  mapViewport {\n    neLat\n    neLong\n    swLat\n    swLong\n    __typename\n  }\n  __typename\n}\n\nfragment MapHitListing on Listing {\n  ...HitListing\n  geoCode {\n    latitude\n    longitude\n    __typename\n  }\n  __typename\n}\n\nfragment FilterCountsSearchRequestResult on SearchResult {\n  id\n  resultCount\n  filterGroups {\n    groupInfo {\n      name\n      id\n      __typename\n    }\n    filters {\n      count @include(if: $filterCounts)\n      checked\n      filter {\n        id\n        name\n        refineByQueryArgument\n        description\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment MapSearchResult on SearchResult {\n  mapViewport {\n    neLat\n    neLong\n    swLat\n    swLong\n    __typename\n  }\n  page\n  pageSize\n  listings {\n    ...MapHitListing\n    __typename\n  }\n  pinnedListing {\n    listing {\n      ...MapHitListing\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PagerSearchResult on SearchResult {\n  fromRecord\n  toRecord\n  pageSize\n  pageCount\n  page\n  resultCount\n  __typename\n}\n\nfragment DestinationMessageSearchResult on SearchResult {\n  destinationMessage(assetVersion: 4) {\n    iconTitleText {\n      title\n      message\n      icon\n      messageValueType\n      link {\n        linkText\n        linkHref\n        __typename\n      }\n      __typename\n    }\n    ...DestinationMessageDestinationMessage\n    __typename\n  }\n  __typename\n}\n\nfragment DestinationMessageDestinationMessage on DestinationMessage {\n  iconText {\n    message\n    icon\n    messageValueType\n    __typename\n  }\n  __typename\n}\n\nfragment ADLSearchResult on SearchResult {\n  parsedParams {\n    q\n    coreFilters {\n      adults\n      children\n      pets\n      minBedrooms\n      maxBedrooms\n      minBathrooms\n      maxBathrooms\n      minNightlyPrice\n      maxNightlyPrice\n      minSleeps\n      __typename\n    }\n    dates {\n      arrivalDate\n      departureDate\n      __typename\n    }\n    sort\n    __typename\n  }\n  page\n  pageSize\n  pageCount\n  resultCount\n  fromRecord\n  toRecord\n  pinnedListing {\n    listing {\n      listingId\n      __typename\n    }\n    __typename\n  }\n  listings {\n    listingId\n    __typename\n  }\n  filterGroups {\n    filters {\n      checked\n      filter {\n        groupId\n        id\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  geography {\n    lbsId\n    name\n    description\n    location {\n      latitude\n      longitude\n      __typename\n    }\n    primaryGeoType\n    breadcrumbs {\n      name\n      countryCode\n      location {\n        latitude\n        longitude\n        __typename\n      }\n      primaryGeoType\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RequestMarkerFragment on Query {\n  requestmarker\n  __typename\n}\n\nfragment SearchTermCarouselSearchResult on SearchResult {\n  discoveryXploreFeeds {\n    results {\n      id\n      title\n      items {\n        ... on SearchDiscoveryFeedItem {\n          type\n          imageHref\n          place {\n            uuid\n            name {\n              full\n              simple\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  typeaheadSuggestion {\n    name\n    __typename\n  }\n  __typename\n}\n\nfragment InternalToolsSearchResult on SearchResult {\n  internalTools {\n    searchServiceUrl\n    __typename\n  }\n  __typename\n}\n\nfragment SEOMetaDataParamsSearchResult on SearchResult {\n  page\n  resultCount\n  pageSize\n  geography {\n    name\n    lbsId\n    breadcrumbs {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment GlobalInlineMessageSearchResult on SearchResult {\n  globalMessages {\n    ...GlobalInlineAlertGlobalMessages\n    __typename\n  }\n  __typename\n}\n\nfragment GlobalInlineAlertGlobalMessages on GlobalMessages {\n  alert {\n    action {\n      link {\n        href\n        text {\n          value\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    body {\n      text {\n        value\n        __typename\n      }\n      link {\n        href\n        text {\n          value\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    id\n    severity\n    title {\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment GlobalBannerContainerSearchResult on SearchResult {\n  globalMessages {\n    ...GlobalBannerGlobalMessages\n    __typename\n  }\n  __typename\n}\n\nfragment GlobalBannerGlobalMessages on GlobalMessages {\n  banner {\n    body {\n      text {\n        value\n        __typename\n      }\n      link {\n        href\n        text {\n          value\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    id\n    severity\n    title {\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment FlexibleDatesSearchResult on SearchResult {\n  percentBooked {\n    currentPercentBooked\n    __typename\n  }\n  __typename\n}\n"
        }


def run(inpts):
    detail_urls = []
    errrs = []
    for inpt in inpts:
        dtails, errs = do_query(inpt)
        detail_urls.extend(dtails)
        errrs.extend(errs)
    dtails = []
    for url in detail_urls:
        print(f'Getting details: {url}')
        time.sleep(randint(1,4))
        try:
            dtails.append(get_property_details(url))
        except:
            continue
    return dtails, errrs

if __name__ == '__main__':
    details, errors = run(inputs)
    now = datetime.now().isoformat().replace(':', '_')
    with open(f'data_{now}.json', 'w') as f:
        json.dump(details, f, indent=2)
    with open(f'errors_{now}.json', 'w') as e:
        json.dump(errors, e, indent=2)
