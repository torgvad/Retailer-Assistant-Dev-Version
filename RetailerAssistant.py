import tkinter
import sqlite3
import threading
import time
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import webbrowser
import psutil
import os
from datetime import date
from datetime import timedelta
import datetime

first_scrape_completed = {}
default_retailer = "Retailer"
default_time = "Time"
default_query = "ID, search name, retailer, excluded, min and max price, max shipping"
retailer_list = [default_retailer, "Property Room", "Ebay", "Goodwill"]
time_interval_list = [default_time, "30 min", "1 hour", "2 hour"]
query_list = [default_query]
current_selected_website = ''
scraper_status = "Scraper is offline"
archive_printing = {4: "Current Bid:", 5: "Shipping cost:", 6: "Price:", 7: "Buy now price:", 8: "Min bid:", 9: "Seller:", 11: "Bid End Date:", 12: "Extra:"}
listing_link_num = 0
link_num = 0
listing_links = {}
links = {}


# if scraper is running kill it
def kill_scraper():
    process_name = "RetailerAssistantScraper.exe"
    for proc in psutil.process_iter():
        try:
            if process_name.lower() in proc.name().lower():
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                messagebox.showinfo("Scraper already dead", "Scraper is already not running.\n")
        except:
            messagebox.showinfo("Scraper already dead", "Scraper is already not running.\n")
    if check_scraper_status():
        scraper_check_label['text'] = "Scraper is online"
    else:
        scraper_check_label['text'] = "Scraper is offline"


# start RetailAssistantScraper.exe and change the label to represent the change
def restart_scraper():
    if check_scraper_status() == False:
        try:
            os.startfile("RetailerAssistantScraper.exe")
        except:
            messagebox.showinfo("Scraper missing", "Scraper missing. You will have to redownload it.\n")
    if check_scraper_status():
        scraper_check_label['text'] = "Scraper is online"
    else:
        scraper_check_label['text'] = "Scraper is offline"


# open a browser to the url of the clicked item in the listing_box
def listing_callback():
    global links
    webbrowser.open_new(listing_links[int(listing_box.tag_names(CURRENT)[0])])


# open a browser to the url of the clicked item in the archive_box
def archive_callback():
    global links
    webbrowser.open_new(links[int(archive_box.tag_names(CURRENT)[0])])


# open a box to inform the user theres excess listings and remove the that query and its archives
def handle_excess_listings(query_id, thread_listing_cursor, thread_listing_connect):
    threaded_query_connect = sqlite3.connect('data/queries.db')
    threaded_query_cursor = threaded_query_connect.cursor()
    threaded_query_cursor.execute('''DELETE from queries WHERE id=?; ''', [query_id])
    threaded_query_connect.commit()
    thread_listing_cursor.execute('''DELETE from listings WHERE query_id=?; ''', [query_id])
    thread_listing_connect.commit()
    error_message = "Query: " + query_list[query_id] + ".\n Is resulting in too many results. The query has been removed. Try more specific search terms.\n"
    query_list.pop(query_id)
    query_select['values'] = query_list
    messagebox.showerror("Excess results", error_message)


# put formatted listing in listing_box
def insert_data_into_listing_box(listing):
    global listing_link_num
    listing_box.insert(END, "Item:\n", (listing_link_num, str(listing_link_num)))
    listing_box.insert(END, "   Name: " + listing[3] + "\n", (listing_link_num, str(listing_link_num)))
    listing_links[listing_link_num] = listing[10]
    listing_box.tag_bind(listing_link_num, "<Button-1>", lambda e: listing_callback())
    i = 4
    while i < 13:
        if listing[i] != "ex" and i != 10:
            listing_box.insert(END, "   " + archive_printing.get(i) + str(listing[i]) + "\n",
                               (listing_link_num, str(listing_link_num)))
            listing_box.tag_bind(listing_link_num, "<Button-1>", lambda e: listing_callback())
        i = i + 1
    listing_box.insert(END, "\n")


# populate first_scrape_completed dict with id: 0
def create_first_scrape_dict():
    global first_scrape_completed
    thread_query_connection = sqlite3.connect('data/queries.db')
    thread_cursor = thread_query_connection.cursor()
    last_query = thread_cursor.execute('''SELECT DISTINCT id from queries;''').fetchall()
    for query in last_query:
        first_scrape_completed[int(query[0])] = 0


# getting distict ids that have just gotten listings and incremenet those id in first_scrape_completed
def adding_onto_first_scrape_dict(new_unique_listings):
    global first_scrape_completed
    for listing in new_unique_listings:
        first_scrape_completed[listing[1]] += 1


# get newly added listings and give error if there are excessive listings
def fetch_listings(thread_listing_cursor, threaded_listing_connect):
    global listing_link_num
    has_been_scraped = []
    purged_listings = []
    query_id_count = {}
    global last_listing, first_scrape_completed
    if len(first_scrape_completed) == 0:
        create_first_scrape_dict()
    if last_listing != None:
        last_listing = int(last_listing)
    else:
        last_listing = 0
    new_listings = thread_listing_cursor.execute('''SELECT * from listings WHERE id > ?;''', (last_listing,)).fetchall()
    new_unique_listings = thread_listing_cursor.execute('''SELECT * from listings WHERE id > ?;''', (last_listing,)).fetchall()
    if len(new_listings) > 0:
        listing_box.configure(state='normal')
        for listing in new_listings:
            try:
                query_id_count[listing[1]] += 1
            except:
                query_id_count[listing[1]] = 1
            has_been_scraped.append(listing[1])
            if query_id_count[listing[1]] > 50 and first_scrape_completed[listing[1]] >= 5 and listing[1] not in purged_listings:
                handle_excess_listings(listing[1], thread_listing_cursor, threaded_listing_connect)
                purged_listings.append(listing[1])
            if listing[1] not in purged_listings:
                insert_data_into_listing_box(listing)
                listing_link_num += 1
        last_listing = thread_listing_cursor.execute('''SELECT MAX(id) from listings;''').fetchone()[0]
        adding_onto_first_scrape_dict(new_unique_listings)
        listing_box.configure(state='disabled')


# check if the scraper exe is currently running
def check_scraper_status():
    process_name = "RetailerAssistantScraper.exe"
    for proc in psutil.process_iter():
        try:
            if process_name.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
    return False


# fetch new listings and add them to the text box and check scraper status
def timed_checker():
    threaded_listing_connect = sqlite3.connect('data/listings.db')
    threaded_listing_cursor = threaded_listing_connect.cursor()
    while True:
        time.sleep(300)
        fetch_listings(threaded_listing_cursor, threaded_listing_connect)
        if check_scraper_status():
            scraper_check_label['text'] = "Scraper is online"
        else:
            scraper_check_label['text'] = "Scraper is offline"


# clear the listings of the currently selected query
def clear_one_archive():
    global query_list, archive_box, last_listing
    archive_box.configure(state='normal')
    if query_select.current() != 0:
        selected_query_id = query_select.get()[:query_select.get().find(",")]
        listing_count = listing_cursor.execute('''SELECT * FROM listings WHERE query_id=?;''', [selected_query_id]).fetchone()
        archive_box.delete('1.0', 'end')
        if listing_count == None:
            archive_box.configure(state='disabled')
            return
        else:
            listing_count = listing_count[0]
        listing_cursor.execute('''DELETE from listings WHERE query_id=?; ''', [selected_query_id])
        listing_connect.commit()
        last_listing = listing_cursor.execute('''SELECT MAX(id) from listings;''').fetchone()[0]
    else:
        messagebox.showinfo("Select query", "You must select a query in order to clear its archives.\n")
    archive_box.configure(state='disabled')


# clear the selected query and its listings
def clear_one_query():
    archive_box.configure(state='normal')
    archive_box.delete('1.0', 'end')
    if query_select.current() != 0:
        selected_query_id = query_select.get()[:query_select.get().find(",")]
        cursor.execute('''DELETE from queries WHERE id=?; ''', [selected_query_id])
        clear_one_archive()
        query_connection.commit()
        query_list.pop(query_select.current())
        query_select['values'] = query_list
    else:
        messagebox.showinfo("Select query", "You must select a query in order to clear one.\n")
    archive_box.configure(state='disabled')
    query_select.current(0)


# delete all queries and listings
def clear_all_queries():
    archive_box.configure(state='normal')
    archive_box.delete('1.0', 'end')
    archive_box.configure(state='disabled')
    listing_cursor.execute('''DELETE FROM listings;''')
    cursor.execute('''DELETE FROM queries;''')
    global last_listing, query_list
    last_listing = 0
    query_list.clear()
    query_list = [default_query]
    query_select['values'] = query_list
    query_select.current(0)
    query_connection.commit()
    listing_connect.commit()


def insert_listing_in_archive_box(listing, link_num):
    global links
    archive_box.insert(END, "Item:\n", (link_num, str(link_num)))
    archive_box.insert(END, "   Name: " + listing[3] + "\n", (link_num, str(link_num)))
    links[link_num] = listing[10]
    archive_box.tag_bind(link_num, "<Button-1>", lambda e: archive_callback())
    i = 4
    while i < 13:
        if (listing[i] != "ex") and i != 10:
            archive_box.insert(END, "   " + archive_printing.get(i) + str(listing[i]) + "\n", (link_num, str(link_num)))
            archive_box.tag_bind(link_num, "<Button-1>", lambda e: archive_callback())
        i = i + 1
    archive_box.insert(END, "\n")


# append the whole listings database to the archive_box
def display_all_archives():
    global links
    archive_box.configure(state='normal')
    link_num = 0
    links.clear()
    archive_box.delete("1.0", "end")
    listings = listing_cursor.execute(''' SELECT * from listings; ''').fetchall()
    for listing in listings:
        insert_listing_in_archive_box(listing, link_num)
        link_num += 1
    archive_box.configure(state='disabled')


# append the archives for the selected query to the archive_BOX
def display_one_archive():
    if query_select.current() == 0:
        return
    global links
    archive_box.configure(state='normal')
    link_num = 0
    links.clear()
    selected_query_id = query_select.get()[:query_select.get().find(",")]
    listings = listing_cursor.execute(''' SELECT * from listings WHERE query_id=?; ''', [selected_query_id]).fetchall()
    archive_box.delete("1.0", "end")
    for listing in listings:
        insert_listing_in_archive_box(listing, link_num)
        link_num += 1
    archive_box.configure(state='disabled')


def show_about():
    about_info = """    I am Vadim Torgashov and this is my 2020 senior capstone for BVU.\n
    This is made with the MIT License.\n
    If you want to see my other projects or get a dev version of this project that you can modify visit my Github:\n
    https://github.com/torgvad\n
    \n\n
    Please read the README.txt if you haven't not read the instructions or cannot remember some of the intricacies.\n"""
    messagebox.showinfo("About", about_info)


# the currently selected query will be added to a .txt in the same folder as the GUI .exe
def convert_to_txt():
    if query_select.current() != 0:
        txt_file = open("saved_archives.txt", "a+")
        all_listings = listing_cursor.execute('''SELECT * FROM listings; ''').fetchall()
        for listing in all_listings:
            # Writes these to file (in order):
                # retailer, name, curr bid, shipping price, buy now price,
                # min bid, seller name, link, bid ending, extra
            txt_file.write("Item:\n")
            txt_file.write("Name: " + listing[3] + "\n")
            i = 4
            while i < 13:
                if str(listing[i]) != "ex" and i != 10:
                    txt_file.write(archive_printing.get(i) + str(listing[i]) + "\n")
                i = i + 1
            txt_file.write("\n\n")
        txt_file.close()
    else:
        messagebox.showinfo("Query no selected", "Please select a query from the list\n")


def check_filter_options():
    if len(min_price_entry.get()) > 0:
        min_price = int(min_price_entry.get())
    else:
        min_price = 0
    if len(max_price_entry.get()) > 0:
        max_price = int(max_price_entry.get())
    else:
        max_price = 5000000000000
    if len(max_shipping_entry.get()) > 0:
        max_ship = int(max_shipping_entry.get())
    else:
        max_ship = 5000000000000
    return [min_price, max_price, max_ship]

# add query to the queries database
def add_request():
    global first_scrape_completed
    listing_box.configure(state='normal')
    if len(cursor.execute('''SELECT * FROM queries WHERE retailer=?;''', [retail_select.get()]).fetchall()) > 25:
        messagebox.showinfo("Excess queries", "You have too many queries for this website, delete some.\n")
        listing_box.configure(state='disabled')
    else:
        # make sure the search bar isn't empty and that the retailer_select and time_interval comboboxes aren't on the default values
        if (min_price_entry.get()).isdigit() == False or (max_price_entry.get()).isdigit() == False or (max_shipping_entry.get()).isdigit() == False:
            if len(min_price_entry.get()) > 0 or len(max_price_entry.get()) > 0 or len(max_shipping_entry.get()) > 0:
                messagebox.showinfo("Not using whole numbers",  "Max shipping cost, minimum price, and maximum price must be only whole numbers\n")
        else:
            if len(search_entry.get()) != 0 and retail_select.get() != default_retailer and time_interval_select.get() != default_time:
                filter_options = check_filter_options()
                cursor.execute('''INSERT INTO queries
                                (search, retailer, exclude, min_price, max_price, shipping, time)
                                VALUES
                                (?, ?, ?, ?, ?, ?, ?);''',
                                [search_entry.get(), retail_select.get(), exclude_entry.get(),
                                   filter_options[0], filter_options[1], filter_options[2], int(time_interval_select.get()[:2])])
                everything = cursor.execute(''' SELECT * from queries; ''').fetchall()
                # take the newly added listing and add it to the query_list with its ID
                cursor.execute('SELECT max(id) FROM queries')
                max_id = cursor.fetchone()[0]
                new_query = (str(max_id), search_entry.get(), retail_select.get(), "exclude:" + exclude_entry.get(),
                            "price:" + min_price_entry.get(), "-" + max_price_entry.get(), "max shipping:" + max_shipping_entry.get())
                query_list.append(','.join(new_query))
                query_select['values'] = query_list
                first_scrape_completed[int(cursor.lastrowid)] = 0
                query_connection.commit()
            else:
                messagebox.showinfo("Not all fields filled", "A Search, Retailer, and Time Interval must be specified\n")
    listing_box.configure(state='disabled')


def first_login_pop_up():
    welcome_info = """    Welcome to the Online Retailer Assistant. This appears to be your first time using the app.\n
    Here are the feature of the program:\n
    The searches tab is used to add new requests.\n
    Simply type in your query, what website you want scraped, select the time interval, and fill in any additional filters.\n
    Be careful with the time interval as excessive results will trigger the program to delete that query.\n
    Seperate words/phrases put in the Exclude field with commas or else the program will interpret what you typed as one continuous phrase.\n
    The large textbox will automatically be populated with new queries which you can click to go to that item's page.\n\n\n
    The queries and data tab allows you to look at existing queries and see what items have already been scraped for it.\n
    Here you can check what queries are being searched for, the item listings for those queries,\n
    Save item listings to a .txt file, or just look at what listings have been scraped\n
    Like the previous tab the items in the large textbox are clickable.\n
    If you need to refer to this intro again click on the "About" button on the bottom left of the window.
    """
    messagebox.showinfo("Welcome", welcome_info)



# Setting up the databases and TKinter
query_connection = sqlite3.connect('data/queries.db')
cursor = query_connection.cursor()
listing_connect = sqlite3.connect('data/listings.db')
listing_cursor = listing_connect.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS queries (
                id integer PRIMARY KEY,
                search text,
                retailer text,
                exclude text,
                min_price interger,
                max_price integer,
                shipping interger,
                time integer
                );''')

listing_cursor.execute(''' CREATE TABLE IF NOT EXISTS listings (
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

listing_cursor.execute('''SELECT * from listings;''')
if listing_cursor.fetchone() is None:
    last_listing = 0
else:
    last_listing = listing_cursor.execute('''SELECT MAX(id) from listings;''').fetchone()[0]

master = Tk()
master.title("Online Retailer Assistant")
master.geometry("935x660")
search_text = "Searches Tab"
queries_text = "Queries and Data Tab"

# Grab all existing queries to add to query_list to display in "Queries and Data" tab
queries = cursor.execute(''' SELECT * from queries; ''').fetchall()
for query in queries:
    # its appending each query's search, retailer, word exclusion, min price, max price, and shipping cost (in order)
    if str(query[5]) == "5000000000000":
        if str(query[6]) == "5000000000000":
            query_list.append(str(query[0]) + "," + ','.join(query[1:3]) + ", exclude:" + query[3] + ", min price:$" +
                                str(query[4]))
        else:
            query_list.append(str(query[0]) + "," + ','.join(query[1:3]) + ", exclude:" + query[3] + ", min price:$" +
                              str(query[4]) + ",max shipping:$" + str(query[6]))
    elif str(query[6]) == "5000000000000":
        query_list.append(str(query[0]) + "," + ','.join(query[1:3]) + ", exclude:" + query[3] + ", min price:$" +
                          str(query[4]) + ",max shipping:$" + str(query[6]))
    else:
        query_list.append(str(query[0]) + "," + ','.join(query[1:3]) + ", exclude:" + query[3] + ",price:$" +
                            str(query[4]) + "-" + str(query[5]) + ",max shipping:$" + str(query[6]))

all_queries = cursor.execute('''SELECT DISTINCT id from queries;''').fetchall()
for query in queries:
    first_scrape_completed[int(query[0])] = 0

tab_parent = ttk.Notebook(master, width=925, height=630)
search_tab = ttk.Frame(tab_parent)
queries_tab = ttk.Frame(tab_parent)
tab_parent.add(search_tab, text=search_text)
tab_parent.add(queries_tab, text=queries_text)
tab_parent.pack()

search_about_button = Button(search_tab, text="About", command=lambda: show_about())
search_about_button.place(x=870, y=590)

query_about_button = Button(queries_tab, text="About", command=lambda: show_about())
query_about_button.place(x=870, y=590)

'''------------------------------Searches tab------------------------------------'''

# Searchbar
search_entry_label = Label(search_tab, text="Search: ")
search_entry_label.place(x=225, y=20)
search_entry = Entry(search_tab, width=70)
search_entry.place(x=275, y=22)

# Retailer selection
retailer_select_label = Label(search_tab, text="Select Retailer: ")
retailer_select_label.place(x=100, y=60)
retail_select = ttk.Combobox(search_tab, values=retailer_list, state='readonly')
retail_select.current(0)
retail_select.place(x=185, y=60)

# price min and max entry
price_label = Label(search_tab, text="Price:")
price_label.place(x=360, y=60)
min_price_entry = Entry(search_tab, width=7)
min_price_entry.place(x=400, y=62)
price_dash = Label(search_tab, text="-")
price_dash.place(x=455, y=60)
max_price_entry = Entry(search_tab, width=7)
max_price_entry.place(x=475, y=62)

# time interval selection
time_label = Label(search_tab, text="Select Time Interval: ")
time_label.place(x=555, y=60)
time_interval_select = ttk.Combobox(search_tab, values=time_interval_list, state='readonly')
time_interval_select.current(0)
time_interval_select.place(x=670, y=60)

# shipping min and max entr
shipping_label = Label(search_tab, text="Max Shipping Cost: ")
shipping_label.place(x=100, y=100)
max_shipping_entry = Entry(search_tab, width=7)
max_shipping_entry.place(x=213, y=102)

# exclude strings from name
exclude_label = Label(search_tab, text="Exclude from title: ")
exclude_label.place(x=293, y=100)
exclude_entry = Entry(search_tab, width=70)
exclude_entry.place(x=400, y=102)

restart_scraper_button = Button(search_tab, text="Restart Scraper", command=lambda: restart_scraper())
restart_scraper_button.place(x=150, y=590)

kill_scraper_button = Button(search_tab, text="Kill Scraper", command=lambda: kill_scraper())
kill_scraper_button.place(x=250, y=590)

scraper_check_label = Label(search_tab, text=scraper_status)
scraper_check_label.place(x=50, y=590)

enter_button = Button(search_tab, text="ENTER", command=lambda: add_request())
enter_button.place(x=425, y=140)

listing_box = Text(search_tab, width=114)
listing_box.configure(state='disabled')
listing_box.place(x=5, y=190)

'''-----------------------------------------Queries tab--------------------------------------------'''

archive_box = Text(queries_tab, width=114)
archive_box.place(x=5, y=190)
archive_box.configure(state='disabled')


# query selector
query_select = ttk.Combobox(queries_tab, values=query_list, state='readonly', width=145)
query_select.place(x=10, y=10)
query_select.bind("<<ComboboxSelected>>", lambda e: display_one_archive())
query_select.current(0)

# Clear queries button
clear_queries_button = Button(queries_tab, text="Clear All Queries", command=lambda: clear_all_queries())
clear_queries_button.place(x=30, y=50)

# Delete select query
clear_selected_button = Button(queries_tab, text="Clear Selected Query", command=lambda: clear_one_query())
clear_selected_button.place(x=400, y=50)

# Clear archive
clear_archive_button = Button(queries_tab, text="Clear Only Query Archives", command=lambda: clear_one_archive())
clear_archive_button.place(x=700, y=50)


# Save archive as .txt
save_archive_button = Button(queries_tab, text="Save selected archive as .txt", command=lambda: convert_to_txt())
save_archive_button.place(x=200, y=100)

# Display all archived data
display_all_button = Button(queries_tab, text="Display all archives", command=lambda: display_all_archives())
display_all_button.place(x=550, y=100)


try:
    start_file = open('data/first.txt', 'r')
    start_file.read()
    start_file.close()
except:
    start_file = open('data/first.txt', 'w+')
    start_file.close()
    first_login_pop_up()



restart_scraper()
threading.Thread(target=timed_checker, daemon=True).start()
mainloop()

