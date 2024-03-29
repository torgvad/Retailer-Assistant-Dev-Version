import requests
import time
import sqlite3
import re
import threading
from urllib import request, response, error, parse
from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import date
from datetime import timedelta
from datetime import datetime
import datetime
import bs4
import random
from fp.fp import FreeProxy
from requests.exceptions import ProxyError
import pyuser_agent


total_sleeps = 1
latest_query_id = 0
webstyles = {}
sleep_time = 1800
scraped_queries = []
# the data structure for storing queries: {retailer: {30: [queryList], 1: [queryList2], 2: [queryList3]}}
queries = {}

default_header = {
    "Accept-Language": "en-US,en;q=0.5",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Accept-Encoding": "br, gzip, deflate",
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
}

current_header = default_header
while True:
    try:
        first_proxy = FreeProxy(country_id=['US']).get()
        break
    except:
        time.sleep(2)
        pass
current_proxy = {"http": first_proxy}


class CustomFormatting:
    @staticmethod
    def format(listing):
        return listing


class CustomFilter:
    @staticmethod
    def filter(filtered_listing, unfiltered_listing):
        return filtered_listing


# use Freeproxy to get new proxy ip and port
# get new user agent
def get_new_header_and_proxy():
    global current_header, current_proxy
    # Occasionally either the useragent or proxy will fail
    # No remediation can be done here other than to just try again
    while True:
        try:
            obj = pyuser_agent.UA()
            current_header["User-Agent"] = obj.chrome
            current_proxy["http"] = FreeProxy(country_id=['US']).get()
            break
        except:
            pass


# take url and insert query and page number
def format_url(link, query):
    page_number_loc = link.find("%d")
    link = str(link)
    query[1] = str(query[1])
    if page_number_loc == -1:
        return link % (query[1])
    if link.find("%s") < page_number_loc:
        return link % (query[1], 1)
    else:
        return link % (1, query[1])


# deletes listings that have dates before today
def remove_listings():
    conn = sqlite3.connect('data/listings.db')
    cursor = conn.cursor()
    full_date = datetime.date.today()
    short_date = full_date.strftime('%Y-%m-%d')
    cursor.execute('''DELETE from listings WHERE ?>bid_end;''', [short_date])
    conn.commit()


# creates global list of queries to track which have already been scraped
def check_number_of_scraped_queries():
    global scraped_queries
    raw_scraped_queries = cursor.execute('''SELECT DISTINCT query_id FROM listings;''').fetchall()
    scraped_queries = []
    for tuple in raw_scraped_queries:
        scraped_queries.append(tuple[0])


# removes queries that no longer exist in database
def clean_removed_queries(queries_cursor):
    distinct_queries = queries_cursor.execute('''SELECT DISTINCT id FROM queries;''').fetchall()
    existing_queries = []
    for tuple in distinct_queries:
        existing_queries.append(int(tuple[0]))
    for time_list in queries:
        for scrape_time in queries[time_list]:
            for query in queries[time_list][scrape_time]:
                if query[0] not in existing_queries:
                    queries[time_list][scrape_time].remove(query)


'''the controller func that grabs queries added while running, 
    deletes queries that have been removed while running, and deletes expired listings'''
def listing_and_query_checker():
    queries_conn = sqlite3.connect('data/queries.db')
    queries_cursor = queries_conn.cursor()
    while True:
        time.sleep(600)
        update_queries(queries_cursor)
        remove_listings()
        clean_removed_queries(queries_cursor)


# check webstyles db to create the webstyles dictionary with webname:data format
def check_webstyles():
    webstyle_list = webstyle_cursor.execute('''SELECT * from webstyles;''').fetchall()
    for webstyle in webstyle_list:
        web_name = webstyle[1]
        value_list = []
        for i in range(2, len(webstyle)):
            value_list.append(webstyle[i])
        webstyles.update({web_name : value_list})


# takes standard link and a partial link that start with "/" and combines them
def format_slash_url(url, slash_link):
    formatted_url = url[8:]
    slash = formatted_url.index("/")
    url = url[:slash+8]
    url = url + slash_link
    return url


class custom_Ebay_filter(CustomFilter):
    @staticmethod
    def filter(filtered_listing, unfiltered_listing):
        if str(unfiltered_listing[0]).find("Shop on eBay") > -1:
            filtered_listing[0] = "ex"
            filtered_listing[2] = "ex"
            return filtered_listing
        #loop through all elements to find newer format changes that need more parsing
        i=0
        for item in filtered_listing:
            if item == "ex" and str(unfiltered_listing[i]).rfind("0-->") != -1:
                temp = str(unfiltered_listing[i])
                temp = temp[temp.rfind("0-->") + 4:]
                temp = temp[:temp.find("<!-")]
                filtered_listing[i] = temp
            i = i + 1
        newer = custom_Ebay_filter.price_shipping_format(filtered_listing)
        return newer
    # further edit any strange edge case HTML formatting
    @staticmethod
    def price_shipping_format(listing):
        shipping = str(listing[2])
        price = str(listing[3])
        if shipping.find("Free") > -1:
            listing[2] = 'ex'
        if str(listing[2]) != 'ex':
            shipping = shipping[2:shipping.find(".")]
            shipping = shipping.replace(",", '')
            if shipping.find('ITALIC">') > -1:
                shipping = shipping[shipping.find(">")+3:]
            listing[2] = shipping
        if price != 'ex':
            if price.find(".") != -1:
                price = price[1:price.find(".")]
            if price.find('ITALIC">') > -1:
                price = price[price.find(">") + 3:]
            listing[3] = price.replace(",", '')
            if len(price) == 0:
                listing[3] = "ex"
        return listing


# call the user-made subclass of CustomFilter if one exists
def CustomFilter_controller(retailer, filtered_listing, unfiltered_listing):
    retailer = retailer.replace(" ", "_")
    try:
        if issubclass(eval("custom_"+retailer+"_filter"), CustomFilter):
            return eval("custom_" + retailer + "_filter").filter(filtered_listing, unfiltered_listing)
        else:
            return filtered_listing
    except:
        return filtered_listing


# find the href assignment
def format_link(link_element, url):
    href = link_element.find('href="')
    past_href = link_element[href + 6:]
    link_element = link_element[href + 6:past_href.find('">') + href + 6]
    link_element = link_element[:link_element.find('"')]
    # if the href isn't a full link and starts with '/' then cat the home page url with the href
    if link_element[0] == "/":
        link_element = format_slash_url(url, link_element)
    return link_element


# get the data inside element and then take out just the number
def format_number(number_element):
    try:
        formatted_str, start_new_index = format_text_in_element(number_element)
        while len(formatted_str.strip()) == 0 and len(formatted_str) > 0:
            number_element = number_element[start_new_index + 1:]
            formatted_str, start_new_index = format_text_in_element(number_element)
        if len(formatted_str) == 0:
            return 'ex'
        formatted_str = formatted_str.replace(",", "")
        number_element = int(re.search(r'\d+', formatted_str).group())
    except:
        number_element = "ex"
    return number_element


# get data inside element as a string
def format_str_element(str_item):
    formatted_str, start_new_index = format_text_in_element(str_item)
    while len(formatted_str.strip()) == 0 and len(formatted_str) > 0:
        str_item = str_item[start_new_index + 1:]
        formatted_str, start_new_index = format_text_in_element(str_item)
    if len(formatted_str) == 0:
        formatted_str = 'ex'
    return formatted_str


# take all of the raw data, trim it, and place it back in the list
# this is where custom formatting is done
def format_elements(element_list, url, website):
    formatted_list = element_list.copy()
    for i in range(0, len(element_list)):
        if formatted_list[i] != "ex":
            str_item = str(formatted_list[i])
            if i == 8:
                str_item = format_link(str_item, url)
            elif i == 1 or i == 2 or i == 3 or i == 6 or i == 7:
                str_item = format_number(str_item)
            else:
                str_item = format_str_element(str_item)
            formatted_list[i] = str_item
    formatted_list = CustomFilter_controller(website, formatted_list, element_list)
    return formatted_list


# do initial scrape
def initial_scrape_new_listing(query):
    webstyle = webstyles[query[2]]
    formated_link = format_url(webstyle[0], query)
    data = run_scrape(query, webstyle, formated_link, query[2])
    if check_id_existance(query[0]):
        add_listing_to_db(query[0], query[2], data)


# take data that exists inside the element
def format_text_in_element(str_item):
    element_name_end = str_item.find(">")
    past_end = str_item[element_name_end:]
    element_end = past_end.find("<")
    str_item = str_item[element_name_end + 1:element_end + element_name_end]
    return str_item, element_name_end


# add the list of queries to their proper place in the data structure (line 23)
def add_queries_to_dict(new_queries, queries_cursor):
    global latest_query_id
    for query in new_queries:
        intermediate_list = list(query)
        intermediate_list[3] = create_exclude_list(query[3])
        query = intermediate_list
        try:
            queries[query[2]][query[7]].append(query)
        except:
            queries[query[2]] = {}
            retailer_val = queries[query[2]]
            retailer_val[30] = []
            retailer_val[1] = []
            retailer_val[2] = []
            retailer_val[query[7]].append(query)
    latest_query_id = queries_cursor.execute('''SELECT MAX(id) from queries;''').fetchone()[0]


# get all queries that exist and add them to the query data structure (line 23)
def check_queries():
    global latest_query_id, queries
    new_queries = queries_cursor.execute('''SELECT * from queries;''').fetchall()
    add_queries_to_dict(new_queries, queries_cursor)


# if the max id is larger than latest_query_id then append it to the queries array
def update_queries(queries_cursor):
    time.sleep(10)
    global latest_query_id
    current_high_id = queries_cursor.execute('''SELECT MAX(id) from queries;''').fetchone()[0]
    if current_high_id != None and current_high_id > latest_query_id:
        new_queries = queries_cursor.execute('''SELECT * from queries where id > ?;''', [latest_query_id]).fetchall()
        add_queries_to_dict(new_queries, queries_cursor)


# given the listing get every element within it
def get_elements(listing, webstyle):
    i = 3
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
            # if the link is an href within the parent element
            if len(parent_element) > 0:
                parent_element = [parent_element[0]]
            if len(parent_element) == 0 and i == 19:
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


# obtain a list of every item listing
def get_every_listing(soup, webstyle):
    html = webstyle[1]
    comma = html.find(",")
    colon = html.find(":")
    element = html[:comma]
    id_type = html[comma + 1:colon]
    name = html[colon + 1:]
    parent_element = soup.findAll(element, {id_type: name})
    depth = int(webstyle[2])
    listings = []
    for elements in parent_element:
        if depth > 0:
            listings.append(elements.findChildren()[depth - 1])
        else:
            listings.append(elements)
    return listings


# take the string saved in the query as terms to exclude
def create_exclude_list(exclude_string):
    if exclude_string.find(',') == -1:
        return [exclude_string]
    comma_list = [i.start() for i in re.finditer(",", exclude_string)]
    exclude_list = [(exclude_string[:comma_list[0]]).strip(), (exclude_string[comma_list[len(comma_list) - 1] + 1:]).strip()]
    for i in range(0, len(comma_list) - 1):
        if i != len(comma_list) - 1:
            exclude_list.append((exclude_string[comma_list[i] + 1:comma_list[i + 1]]).strip())
    return exclude_list


# will filter list based on query list, returns false if any of the elements fail
def filter_results(listing_elements, query):
    for exclude in query[3]:
        if len(exclude) == 0:
            break
        if exclude.lower() in listing_elements[0].lower():
            return False
    if listing_elements[1] != "ex" and (int(listing_elements[1]) < query[4] or int(listing_elements[1]) > query[5]):
        return False
    elif listing_elements[2] != 'ex' and int(listing_elements[2]) > query[6]:
        return False
    elif listing_elements[3] != "ex" and (int(listing_elements[3]) < query[4] or int(listing_elements[3]) > query[5]):
        return False
    elif listing_elements[6] != "ex" and (int(listing_elements[6]) < query[4] or int(listing_elements[6]) > query[5]):
        return False
    elif listing_elements[7] != "ex" and (int(listing_elements[7]) < query[4] or int(listing_elements[7]) > query[5]):
        return False
    return True


# checks if id exists
def check_id_existance(id):
    t_conn = sqlite3.connect('data/queries.db')
    t_cursor = t_conn.cursor()
    id_check = t_cursor.execute('''SELECT * from queries WHERE id=?;''', [id]).fetchone()
    t_conn.close
    if id_check != None:
        return True
    else:
        return False


# get all the elements in the listings, filter them, and return them
def get_listings(all_listings, webstyle, url, query, website):
    all_listing_elements = []
    for listing in all_listings:
        if type(listing) is not bs4.element.Comment and type(listing) != 'NoneType':
            listing_elements = get_elements(listing, webstyle)
            listing_elements = format_elements(listing_elements, url, website)
            if listing_elements[0] != "ex" and filter_results(listing_elements, query) == True:
                all_listing_elements.append(listing_elements)
    return all_listing_elements


# take the given query and webstyle and run the actual scrape
def run_scrape(query, webstyle, url, website):
    global current_header, current_proxy, default_header
    attempt_counter = 0
    while True:
        time.sleep(2)
        try:
            res = requests.get(url, headers=current_header, proxies=current_proxy, timeout=6)
            res.raise_for_status()
            if res.status_code == 404:
                raise Exception
            break
        except:
            get_new_header_and_proxy()
        attempt_counter += 1
        if attempt_counter >= 20:
            res = requests.get(url, headers=default_header)
            break
    soup = BeautifulSoup(res.text, 'html.parser')
    all_listings = get_every_listing(soup, webstyle)
    return get_listings(all_listings, webstyle, url, query, website)


class custom_Ebay_formatting(CustomFormatting):
    @staticmethod
    def format(listing):
        extended_date = date.today()
        if listing[4] != "ex":
            time_left = listing[4][:listing[4].find(" ")]
            if "d" in time_left:
                extended_date += timedelta(days=int(time_left[:time_left.find("d")]))
                if "h" in listing[4] and int(listing[4][listing[4].find(" ")+1:listing[4].find("h")]) + datetime.datetime.now().hour >= 24:
                    extended_date += timedelta(days=1)
            elif "h" in time_left:
                if (int(time_left[:time_left.find("h")]) + datetime.datetime.now().hour) >= 24:
                    extended_date += timedelta(days=1)
            else:
                if datetime.datetime.now().hour == 23 and (int(time_left[:time_left.find("m")]) + datetime.now().minute) >= 60:
                    extended_date += timedelta(days=1)
            listing[4] = extended_date.strftime('%Y-%m-%d')
        if listing[5].startswith("Seller: "):
            listing[5] = listing[5][8:]
        if listing[9] != "ex":
            listing[1] = listing[3]
            listing[3] = "ex"
        if 'Shop on eBay' in listing[0]:
            return False
        return listing


class custom_Rubylane_formatting(CustomFormatting):
    @staticmethod
    def format(listing):
        listing[8] = listing[8][:listing[8].find(";t")]
        return listing


class custom_Property_Room_formatting(CustomFormatting):
    @staticmethod
    def format(listing):
        time_left = listing[4]
        remaining_time = 0
        try:
            remaining_time = int(time_left[0])
        except:
            return False
        if listing[4].find('d') != -1:
            extended_date = date.today() + timedelta(days=remaining_time)
        elif listing[4].find('h') != -1:
            extended_date = date.today() + timedelta(hours=int(time_left[0:1]))
        else:
            return False
        listing[4] = extended_date.strftime('%Y-%m-%d')
        return listing


# use the user created subclass of CustomFormatting if one exists
def last_minute_formatting(listing, retailer):
    retailer = retailer.replace(" ", "_")
    try:
        if issubclass(eval("custom_"+retailer+"_formatting"), CustomFormatting):
            return eval("custom_" + retailer + "_formatting").format(listing)
        else:
            return listing
    except:

        return listing


# take the listings and their corresponding query_id and add them to the listings.db
def add_listing_to_db(query_id, retailer, listings):
    t_conn = sqlite3.connect('data/listings.db')
    t_cursor = t_conn.cursor()
    for listing in listings:
        listing = last_minute_formatting(listing, retailer)
        if listing != False:
            db_match = t_cursor.execute("""SELECT * from listings where link=? and retailer=? and query_id=?;""",
                                        [listing[8], retailer, query_id]).fetchone()
            if db_match == None:
                t_cursor.execute("""INSERT INTO listings
                                (query_id, retailer, name, bid, shipping_cost, current_price, 
                                bid_end, seller_name, buy_now_price, min_bid, link, extra)
                                VALUES
                                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                               [query_id, retailer, listing[0], listing[1], listing[2], listing[3],
                                listing[4], listing[5], listing[6], listing[7], listing[8], listing[9]])
            else:
                t_conn.commit()
                return False
    t_conn.commit()
    t_conn.close()
    return True


# runs until reaches the oldest item or the 5th page
def cycle_through_pages(query, webstyle):
    web_name = query[2]
    i = 1
    page_number_loc = webstyle[0].find("%d")
    if page_number_loc == -1:
        url = webstyle[0] % query[1]
        data = run_scrape(query, webstyle, url)
        if check_id_existance(query[0]):
            add_listing_to_db(query[0], data)
        return
    search_loc = webstyle[0].find("%s")
    while i < 5:
        time.sleep(random.randint(4, 10))
        if search_loc < page_number_loc:
            data = run_scrape(query, webstyle, webstyle[0] % (query[1], i), web_name)
        else:
            data = run_scrape(query, webstyle, webstyle[0] % (i, query[1]), web_name)
        if check_id_existance(query[0]):
            if add_listing_to_db(query[0], web_name, data) == False:
                return
        i += 1


# go through all the queries in the array and scrape them appropriately
def initiate_scrapes_in_retailer_dict(queries):
    global scraped_queries
    for query in queries:
        if query[0] in scraped_queries:
            cycle_through_pages(query, webstyles[query[2]])
        else:
            initial_scrape_new_listing(query)
            scraped_queries.append(query[0])


# given the dictionary with time:queryList pairs scrape the ones that should be scraped in this cycle
def cycle_through_retailers_dict(queries_dict, sleeps):
    initiate_scrapes_in_retailer_dict(queries_dict[30])
    if sleeps == 2:
        initiate_scrapes_in_retailer_dict(queries_dict[1])
    elif sleeps >= 4:
        initiate_scrapes_in_retailer_dict(queries_dict[2])
        initiate_scrapes_in_retailer_dict(queries_dict[1])


# open threads to scrape each retailer in their own thread
# this is the start of the scraping process
def scrape():
    global total_sleeps
    while True:
        time.sleep(sleep_time)
        get_new_header_and_proxy()
        for retailer_list in queries:
            threading.Thread(target=cycle_through_retailers_dict, args=(queries[retailer_list], total_sleeps), daemon=True).start()
        time.sleep(2)
        total_sleeps += 1
        if total_sleeps > 4:
            total_sleeps = 1


conn = sqlite3.connect('data/listings.db')
cursor = conn.cursor()

webstyle_conn = sqlite3.connect('data/webstyles.db')
webstyle_cursor = webstyle_conn.cursor()

queries_conn = sqlite3.connect('data/queries.db')
queries_cursor = queries_conn.cursor()

cursor.execute(''' CREATE TABLE IF NOT EXISTS listings (
                            id integer PRIMARY KEY,
                            query_id integer,
                            retailer text,
                            name text,
                            bid integer,
                            shipping_cost integer,
                            current_price integer,
                            buy_now_price integer,
                            min_bid integer,
                            seller_name text,
                            link text,
                            bid_end text,
                            extra text );''')

queries_cursor.execute('''CREATE TABLE IF NOT EXISTS queries (
                id integer PRIMARY KEY,
                search text,
                retailer text,
                exclude text,
                min_price interger,
                max_price integer,
                shipping interger,
                time integer
                );''')

check_number_of_scraped_queries()
check_webstyles()
check_queries()

latest_query_id = queries_cursor.execute('''SELECT MAX(id) from queries;''').fetchone()[0]
if latest_query_id == None:
    latest_query_id = 0
threading.Thread(target=listing_and_query_checker, daemon=True).start()
scrape()
conn.close()
webstyle_conn.close()
queries_conn.close()