import logging
from datetime import datetime
import requests
from crawler.spiders.base import BaseSpider

logger = logging.getLogger(__name__)

API = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"


class PL3Spider(BaseSpider):
    lottery_code = "pl3"

    def fetch(self, page_size=1):
        resp = requests.get(
            API,
            params={"gameNo": 35, "provinceId": 0, "pageSize": page_size, "isVerify": 1, "pageNo": 1},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Referer": "https://www.sporttery.cn/",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://www.sporttery.cn",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def parse(self, raw):
        items = []
        for r in raw.get("value", {}).get("list", []):
            try:
                digits = [int(x) for x in r["lotteryDrawResult"].split()]
                items.append({
                    "issue": r["lotteryDrawNum"],
                    "draw_date": datetime.strptime(r["lotteryDrawTime"][:10], "%Y-%m-%d").date(),
                    "numbers": {"digits": digits},
                    "sales_amount": str(r.get("totalSaleAmount", "")),
                    "pool_amount": str(r.get("poolBalanceAfterdraw", "")),
                    "prize_grades": [
                        {"level": g["prizeLevel"], "count": g["stakeCount"], "amount": g["stakeAmount"]}
                        for g in r.get("prizeLevelList", [])
                    ],
                })
            except Exception:
                logger.error("parse pl3 记录解析失败, 跳过: %r", r.get("lotteryDrawNum", r), exc_info=True)
                continue
        return items
