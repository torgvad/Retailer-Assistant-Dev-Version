import sqlite3

conn = sqlite3.connect('data/webstyles.db')
cursor = conn.cursor()


#adding this in to make git see changes

def restore_ebay():
    website = 'https://www.ebay.com/sch/i.html?_from=R40&_nkw=%s&_sacat=0&LH_TitleDesc=0&LH_All=1&_ipg=240&_pgn=%d'
    retailer_name = "Ebay"
    listing_html = "div,class:s-item__info clearfix"
    listing_depth = 0
    title_html = "div,class:s-item__title"
    title_depth = 1
    curr_bid_html = "ex"
    curr_bid_depth = 0
    shipping_html = "span,class:s-item__shipping s-item__logisticsCost"
    shipping_depth = 0
    price_html = "span,class:s-item__price"
    price_depth = 0
    bid_end_html = "span,class:s-item__time-left"
    bid_end_depth = 0
    seller_html = "span,class:s-item__seller-info-text"
    seller_depth = 0
    buy_now_price_html = "ex"
    buy_now_price_depth = 0
    min_bid_html = "ex"
    min_bid_depth = 0
    link_html = "a,class:s-item__link"
    link_depth = 0
    extra_html = "span,class:s-item__bids s-item__bidCount"
    extra_depth = 0
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


def restore_rubylane():
    website = 'https://www.rubylane.com/ni/search?ipp=180&page=%d&q=%s&sort=newest&style=3'
    retailer_name = "Rubylane"
    listing_html = "div,class:settings-group"
    listing_depth = 0
    title_html = "span,class:lvtitle"
    title_depth = 0
    curr_bid_html = "ex"
    curr_bid_depth = 0
    shipping_html = "ex"
    shipping_depth = 0
    price_html = "div,class:lvprice text-xs-center"
    price_depth = 0
    bid_end_html = "ex"
    bid_end_depth = 0
    seller_html = "ex"
    seller_depth = 0
    buy_now_price_html = "ex"
    buy_now_price_depth = 0
    min_bid_html = "ex"
    min_bid_depth = 0
    link_html = "a,style:padding: 10px 0;"
    link_depth = 0
    extra_html = "ex"
    extra_depth = 0
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


def restore_prop_room():
    website = 'https://www.propertyroom.com/s/%s/%d#scrollcontainer'
    retailer_name = "Property Room"
    listing_html = "div,class:product-details-container-category"
    listing_depth = 0
    title_html = "div,class:product-name-category"
    title_depth = 1
    curr_bid_html = "div,class:time-bids-category"
    curr_bid_depth = 3
    shipping_html = "ex"
    shipping_depth = 0
    price_html = "ex"
    price_depth = 0
    bid_end_html = "div,class:time-bids-category"
    bid_end_depth = 2
    seller_html = "ex"
    seller_depth = 0
    buy_now_price_html = "ex"
    buy_now_price_depth = 0
    min_bid_html = "ex"
    min_bid_depth = 0
    link_html = "div,class:product-name-category"
    link_depth = 1
    extra_html = "ex"
    extra_depth = 0
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


restore_ebay()
restore_rubylane()
restore_prop_room()