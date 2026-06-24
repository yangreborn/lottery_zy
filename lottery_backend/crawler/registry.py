from crawler.spiders.ssq import SsqSpider
from crawler.spiders.dlt import DltSpider
from crawler.spiders.kl8 import KL8Spider
from crawler.spiders.td import TDSpider
from crawler.spiders.pl3 import PL3Spider

SPIDERS = {"ssq": SsqSpider, "dlt": DltSpider, "kl8": KL8Spider, "3d": TDSpider, "pl3": PL3Spider}
