import sqlite3
import requests
from urllib import request, response, error, parse
from urllib.request import urlopen
from bs4 import BeautifulSoup
import bs4
import re


testing = False

if testing == True:
    conn = sqlite3.connect('data/webstyles_test.db')
    cursor = conn.cursor()
else:
    conn = sqlite3.connect('data/webstyles.db')
    cursor = conn.cursor()

test_search = "purse"

website = 'ex'
retailer_name = "ex"
listing_html = "ex"
listing_depth = 0
title_html = "ex"
title_depth = 0
curr_bid_html = "ex"
curr_bid_depth = 0
shipping_html = "ex"
shipping_depth = 0
price_html = "ex"
price_depth = 0
bid_end_html = "ex"
bid_end_depth = 0
seller_html = "ex"
seller_depth = 0
buy_now_price_html = "ex"
buy_now_price_depth = 0
min_bid_html = "ex"
min_bid_depth = 0
link_html = "ex"
link_depth = 0
extra_html = "ex"
extra_depth = 0


cursor.execute(''' CREATE TABLE IF NOT EXISTS webstyles (
                id integer PRIMARY KEY,
                retailer text,
                website text,
                listing_html,
                listing_depth,
                title text,
                title_depth depth,
                curr_bid text,
                curr_bid_depth integer,
                shipping_cost text,
                shipping_cost_depth integer,
                price text,
                price_depth integer, 
                bid_end text,
                bid_end_depth integer,
                seller text,
                seller_depth integer,
                buy_now_price text,
                buy_now_depth integer,
                min_bid text,
                min_bid_depth integer,
                link text,
                link_depth integer,
                extra text,
                extra_depth integer
                );''')

cursor.execute(''' INSERT INTO webstyles
                (retailer, website, listing_html, listing_depth, 
                title, title_depth, curr_bid, curr_bid_depth, 
                shipping_cost, shipping_cost_depth, price, 
                price_depth, bid_end, bid_end_depth, seller, 
                seller_depth, buy_now_price, buy_now_depth, 
                min_bid, min_bid_depth, link, link_depth,  extra, extra_depth)
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''',
               [retailer_name, website, listing_html, listing_depth, title_html, title_depth, curr_bid_html,
                curr_bid_depth, shipping_html, shipping_depth, price_html, price_depth, bid_end_html, bid_end_depth,
                seller_html, seller_depth, buy_now_price_html, buy_now_price_depth, min_bid_html, min_bid_depth,
                link_html, link_depth, extra_html, extra_depth])

conn.commit()

"""-------test goes here--------"""


def get_every_listing(soup, webstyle):
    html = webstyle[3]
    comma = html.find(",")
    colon = html.find(":")
    element = html[:comma]
    id_type = html[comma + 1:colon]
    name = html[colon + 1:]
    parent_element = soup.findAll(element, {id_type: name})
    depth = int(webstyle[4])
    listings = []
    for elements in parent_element:
        for element in elements:
            if len(element) > 1:
                if depth > 0:
                    listings.append(element.findChildren()[depth - 1])
                else:
                    listings.append(element)
    return listings


def get_elements(listing, webstyle):
    i = 5
    element_list = []
    while i < len(webstyle):
        if webstyle[i] != "ex":
            depth = int(webstyle[i+1])
            html = webstyle[i]
            comma = html.find(",")
            colon = html.find(":")
            element = html[:comma]
            id_type = html[comma+1:colon]
            name = html[colon+1:]
            parent_element = listing.findAll(element, {id_type: name})
            if len(parent_element) == 0 and i == 21:
                str_listing = str(listing)
                parent_element = str_listing[:str_listing.find(">")]
                parent_element = parent_element + '">'
                element_list.append(parent_element)
            else:
                if len(parent_element) == 0:
                    element_list.append("ex")
                for element in parent_element:
                    if depth > 0:
                        element_list.append(element.findChildren()[depth-1])
                    else:
                        element_list.append(element)
        else:
            element_list.append("ex")
        i += 2
    return element_list


def format_text_in_element(str_item):
    element_name_end = str_item.find(">")
    past_end = str_item[element_name_end:]
    element_end = past_end.find("<")
    str_item = str_item[element_name_end + 1:element_end + element_name_end]
    return str_item, element_name_end


def format_slash_url(url, slash_link):
    formatted_url = url[8:]
    slash = formatted_url.index("/")
    url = url[:slash+8]
    url = url + slash_link
    return url

def format_elements(element_list, url, website):
    for i in range(0, len(element_list)):
        if element_list[i] != "ex":
            str_item = str(element_list[i])
            if i == 8:
                href = str_item.find('href="')
                past_href = str_item[href+6:]
                str_item = str_item[href+6:past_href.find('">')+href+6]
                str_item = str_item[:str_item.find('"')]
                if str_item[0] == "/":
                    str_item = format_slash_url(url, str_item)
            elif i == 1 or i == 2 or i == 3 or i == 6 or i == 7:
                try:
                    formatted_str, start_new_index = format_text_in_element(str_item)
                    while len(formatted_str.strip()) == 0:
                        str_item = str_item[start_new_index + 1:]
                        formatted_str, start_new_index = format_text_in_element(str_item)
                    str_item = formatted_str
                    str_item = int(re.search(r'\d+', str_item).group())
                except:
                    str_item = "ex"
            else:
                formatted_str, start_new_index = format_text_in_element(str_item)
                while len(formatted_str.strip()) == 0 and len(formatted_str) > 0:
                    str_item = str_item[start_new_index + 1:]
                    formatted_str, start_new_index = format_text_in_element(str_item)
                if len(formatted_str) == 0:
                    formatted_str = 'ex'
                str_item = formatted_str
            element_list[i] = str_item
    return element_list


def format_link(link, search, page):
    try:
        page_number_loc = link.find("%d")
    except:
        return link % search
    search_loc = link.find("%s")
    if search_loc < page_number_loc:
        return link % (search, page)
    else:
        return link.format(page, search)

def test(search, site):
    webstyle = cursor.execute('''SELECT * FROM webstyles WHERE retailer=?''', [site]).fetchone()
    url = format_link(webstyle[2], search, 1)
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    print(url)
    res = requests.get(url, headers=header)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    listings = get_every_listing(soup, webstyle)
    all_listings = []
    for listing in listings:
        if type(listing) is not bs4.element.Comment:
            all_listings.append(format_elements(get_elements(listing, webstyle), url, site))
    for listing in all_listings:
        print(listing)

#test(test_search, retailer_name)
if testing == True:
    test(test_search, retailer_name)
    cursor.execute('''DROP TABLE webstyles;''')
    conn.commit()