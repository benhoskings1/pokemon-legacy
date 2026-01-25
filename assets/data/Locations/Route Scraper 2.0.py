import time

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.firefox.options import Options as FirefoxOptions


class Scraper:
    def __init__(self, header=False):
        options = FirefoxOptions()
        if not header:
            options.add_argument("--headless")
        self.driver = webdriver.Firefox(options=options)
        self.driver.get("https://bulbapedia.bulbagarden.net/wiki/Main_Page")

    def scrapeRoute(self, num):
        self.driver.get(str.format("https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_{}", num))
        time.sleep(3)
        tables = pd.read_html(self.driver.page_source)
        print(tables)

    def close(self):
        self.driver.close()


scraper = Scraper(header=True)
scraper.scrapeRoute(201)
scraper.close()