# -*- coding: utf-8 -*-
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import googlemaps
from requests import get
from time import sleep
from sys import argv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from datetime import datetime


def internallinks(url, number_of_pages):
    """This method is perform to extract all the pages of the site """
    hotelslist = set()
    request = get(url)
    parser = BeautifulSoup(request.text, 'html.parser')
    page_load = 5
    for link in parser.findAll("a", href=re.compile("^(/|.*)(?=REVIEWS)")):
        if link.attrs['href'] is not None:
            hotelurl = link.attrs['href']
            url = 'https://www.tripadvisor.es' + str(hotelurl)
            hotelslist.add(url)
        else:
            pass
    next_page = parser.find(class_="prw_rup prw_common_standard_pagination_resp").find("a", href=re.compile("^(/|.*)"))
    next_page_url = next_page.attrs['href']
    while number_of_pages > 1:
        url = 'https://www.tripadvisor.es' + str(next_page_url)
        request = get(url)
        parser = BeautifulSoup(request.text, 'html.parser')
        for link in parser.findAll("a", href=re.compile("^(/|.*)(?=REVIEWS)")):
            if link.attrs['href'] is not None:
                hotelurl = link.attrs['href']
                url = 'https://www.tripadvisor.es' + str(hotelurl)
                hotelslist.add(url)
            else:
                pass
        try:
            next_page = parser.find(class_="prw_rup prw_common_standard_pagination_resp").find("a", href=re.compile(
                "^(/|.*)"))
            next_page_url = next_page.attrs['href']
            print(next_page_url)
            number_of_pages = number_of_pages - 1
            if page_load < 5:
                page_load = page_load + (5 - page_load)
            else:
                pass
        except:
            print(
                "IndexError(Encontramos un error al extraer la  {0} página volvemos a ejecutar el contenido de esa "
                "pagina)".format(str(number_of_pages)))
            sleep(1)
            if page_load > 0:
                page_load = page_load - 1
                pass
            else:
                raise IndexError("Encontramos un error al extraer la  {0} multiples fallos "
                                 "salimos ").format(str(number_of_pages))
    return hotelslist

@asyncio.coroutine
async def gethotelsinfo(url, key):
    """This method it is perform to retrieve a list with all the information of the hotels.Asynchronous Request."""
    async with aiohttp.ClientSession() as client:
        response = await  client.request('GET', url)
        text = await  response.read()
        # we create a google maps object.
        gmaps = googlemaps.Client(key=key)
        parser = BeautifulSoup(text, 'html.parser')
        current_timestamp_utc = datetime.utcnow()
        hotelreview = {}
        hotelreview.update({'url':url,'insert_time_utc':current_timestamp_utc})
        # name
        try:
            name = parser.find(class_="heading_title").get_text()
            title = re.sub('\n', '', name)
        except:
            title = None
        hotelreview.update({'title':title})
        # address
        try:
            address = parser.find(class_="content hidden").get_text('')
        except:
            address = None
        hotelreview.update({'address':address})
        # latitude and longitude
        if address is None:
            latitude = None
            longitude = None
            hotelreview.update({'location': None})
        else:
            try:
                # we make the request to the google maps API.
                geocode_result = gmaps.geocode(address)
                latitude = geocode_result[0]['geometry']['location']['lat']
                longitude = geocode_result[0]['geometry']['location']['lng']
                hotelreview.update({'location': str(latitude) + ',' + str(longitude)})
            except:
                latitude = None
                longitude = None
                hotelreview.update({'location':None})
        # zipcode.
        try:
            raw_zipcode = parser.find(class_="content hidden").find(class_="locality").get_text('')
            zipcode = int(raw_zipcode.split(' ')[0])
        except:
            zipcode = None
        hotelreview.update({'zipcode':zipcode})
        # city
        try:
            raw_city = parser.find(class_="content hidden").find(class_="locality").get_text('')
            city = raw_city.split(' ')[1].replace(',', '')
        except:
            city = None
        hotelreview.update({'city':city})
        # rooms
        try:
            numberofrooms = int(parser.find(class_="list number_of_rooms").get_text(';').split(';')[1])
        except:
            numberofrooms = None
        hotelreview.update({'numberofrooms':numberofrooms})
        # stars
        try:
            stars = parser.find(class_="starRating detailListItem").get_text(';').split(';')[1]
        except:
            stars = None
        hotelreview.update({'stars':stars})
        # services
        try:
            service = str([i.get_text(';') for i in parser.find(class_="detailsMid").
                          findAll(class_="highlightedAmenity detailListItem")]).replace("'", "")
        except:
            service = None
        hotelreview.update({'service':service})
        # price
        try:
            prices = parser.find(class_="list price_range").get_text(';').replace('\xa0', '')
            minprice = int(prices.split(';')[1].split('€')[0])
            maxprice = int(prices.split(';')[1].split('-')[1].split("€")[0])
        except:
            minprice = None
            maxprice = None
        hotelreview.update({'minprice':minprice})
        hotelreview.update({'maxprice':maxprice})
        #phonenumber
        try:
            phone = parser.find(class_="blEntry phone").get_text()
            parse_phone = "".join(phone.split())
        except:
            parse_phone = None
        hotelreview.update({'parse_phone':parse_phone})
        return hotelreview


def main():
    if len(argv) == 4:
        # parameters
        url = argv[1]
        gmapskey = argv[2]
        numberofpages = int(argv[3])
        # tripadvisorcrwaler
        #async request.
        listlinks = internallinks(url, numberofpages)
        coroutine = []
        for url in listlinks:
            coroutine.append(asyncio.Task(gethotelsinfo(url, gmapskey)))
        all_task=asyncio.gather(*coroutine, return_exceptions=True)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(all_task)
        # insert a elasticsearch object.
        es=Elasticsearch()
        # execute multiple inserts.
        actions = ({"_index":"tripadvisor","_type":"review","_id":i.result()['url'],"_source":i.result()}
                   for i in coroutine if i.exception() is None)
        #create an elastic search object, by default.
        success, _ = bulk(es, actions, index="tripadvisor", raise_on_error=True)
        print(success)
    else:
        print("Los parametros se estan introduciendo mal")
if __name__ == "__main__":
    main()