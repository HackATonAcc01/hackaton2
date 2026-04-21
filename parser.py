import lxml.html
import lxml.etree
class Parser:
    def __init__(self, shops):
        self.shops = shops
        self.all_prices = {}
    def kupikod(self):
        try:
            parser_gl = lxml.html.fromstring(self.shops["kupikod_gl"])
            price_gl = parser_gl.xpath('//p[@class="price__card-new"]/text()')[0]
            parser_rucis = lxml.html.fromstring(self.shops["kupikod_rucis"])
            price_rucis = parser_rucis.xpath('//p[@class="price__card-new"]/text()')[0]
            self.all_prices["kupikod_gl"] = price_gl.replace("₽\xa0", "")
            self.all_prices["kupikod_rucis"] = price_rucis.replace("₽\xa0", "")
        except IndexError:
            print("kupikod is empty")

            


    def steam_account(self):
        try:
            parser = lxml.html.fromstring(self.shops["steam_account"])
            price = parser.xpath('//span[@itemprop="price"]/text()')
            availability = parser.xpath('//span[@class="presense-info__status"]/text()')
            parser_alt = lxml.html.fromstring(self.shops["steam_account_alt"])
            price_alt = parser_alt.xpath('//span[@itemprop="price"]/text()')
            availability_alt = parser.xpath('//span[@class="presense-info__status"]/text()')
            print(availability, " ", availability_alt)
            if "Товар закончился" in ''.join(availability):
                price = None
            if "Товар закончился" in ''.join(availability_alt):
                price_alt = None
            self.all_prices["steam_account"] = price
            self.all_prices["steam_account"] = price_alt
        except IndexError:
            print("steam account is empty")
    def steam_buy(self):
        try:
            parser = lxml.html.fromstring(self.shops["steam_buy"])
            price = parser.xpath('//div[@class="product-price__cost"]/text()')
            self.all_prices["steam_buy"] = price[0].replace(" р", "")
        except IndexError:
            print("steam buy is empty")
    def steam_pay(self):
        try:
            parser = lxml.html.fromstring(self.shops["steam_pay"])
            price = parser.xpath('//div[@class="product__current-price"]/text()')
            self.all_prices["steam_pay"] = price[0].replace(" ", "").replace('\n', "")
        except IndexError:
            print("steam pay is empty")
    def prices(self):
        self.kupikod()
        self.steam_account()
        self.steam_pay()
        self.steam_buy()
        return self.all_prices
