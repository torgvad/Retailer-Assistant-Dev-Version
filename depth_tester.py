import requests
from urllib import request, response, error, parse
from urllib.request import urlopen
from bs4 import BeautifulSoup


url = "https://www.ebay.com/sch/i.html?_from=R40&_nkw=watch&_sacat=0&LH_TitleDesc=0&_sop=10&_ipg=200&_pgn=1"
element = "h3"
id_type = "class"
name = "s-item__title"
depth = 0


header = {
    "Accept-Language": "en-US,en;q=0.5",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Accept-Encoding": "br, gzip, deflate",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", }
res = requests.get(url, headers=header)
res.raise_for_status()
soup = BeautifulSoup(res.text, 'html.parser')
# Uncomment the print below to see all html data that beatifulsoup has received.
# It may be different than what you see using the inspect element on a browser
#print(soup)
element_list = []
parent_elements = soup.findAll(element, {id_type: name})
if depth > 0:
    for element in parent_elements:
        element_list.append(element.findChildren()[depth - 1])
    for item in element_list:
        print(item)
else:
    for element in parent_elements:
        print(element)

