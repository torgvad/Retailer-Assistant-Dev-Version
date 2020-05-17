import requests
from urllib import request, response, error, parse
from urllib.request import urlopen
from bs4 import BeautifulSoup


url = "https://www.shopgoodwill.com/Listings?st=purse&sg=&c=&s=&lp=0&hp=999999&sbn=False&spo=False&snpo=False&socs=False&sd=False&sca=False&cadb=7&scs=False&sis=False&col=1&p=3&ps=40&desc=True&ss=0&UseBuyerPrefs=true"
element = "a"
id_type = "class"
name = "product"
depth = 0


header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", }
res = requests.get(url, headers=header)
res.raise_for_status()
soup = BeautifulSoup(res.text, 'html.parser')
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

