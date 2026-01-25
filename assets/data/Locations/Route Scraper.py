import requests
from bs4 import BeautifulSoup


def getdata(url):
    r = requests.get(url)
    return r.text


def scrapeData(routeName):
    try:
        htmldata = getdata(str.format("https://pokemondb.net/location/sinnoh-route-{}", routeName))
    except KeyError:
        print("Key error")
        return

    soup = BeautifulSoup(htmldata, 'html.parser')
    print(soup.prettify())
    headerIdx = 1
    headers = []
    while True:
        header = soup.find(str.format("h{}", headerIdx))
        if header:
            print(header.text, headerIdx)
            headerIdx += 1
        else:
            break

    tables = soup.find_all("table", class_="data-table")
    for table in tables:
        print(soup.find("h2"))

    return None


data = scrapeData(201)
