from abc import ABC, abstractmethod


class BaseSpider(ABC):
    """每个彩种一个 spider 子类，设 lottery_code，实现 fetch/parse。"""
    lottery_code = None

    @abstractmethod
    def fetch(self):
        """抓取原始数据，返回 str 或 dict。"""

    @abstractmethod
    def parse(self, raw):
        """解析为统一结构 list[dict]。"""

    def run(self):
        return self.parse(self.fetch())
