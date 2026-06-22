import logging
from datetime import datetime
import requests
from crawler.spiders.base import BaseSpider

logger = logging.getLogger(__name__)

API = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"


class DltSpider(BaseSpider):
    lottery_code = "dlt"

    def fetch(self, page_size=1):
        resp = requests.get(
            API,
            params={"gameNo": 85, "provinceId": 0, "pageSize": page_size, "isVerify": 1, "pageNo": 1},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.sporttery.cn/"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def parse(self, raw):
        items = []
        for r in raw.get("value", {}).get("list", []):
            nums = [int(x) for x in r["lotteryDrawResult"].split()]
            items.append({
                "issue": r["lotteryDrawNum"],
                "draw_date": datetime.strptime(r["lotteryDrawTime"][:10], "%Y-%m-%d").date(),
                "numbers": {"red": nums[:5], "blue": nums[5:7]},
                "sales_amount": str(r.get("totalSaleAmount", "")),
                "pool_amount": str(r.get("poolBalanceAfterdraw", "")),
                "prize_grades": [
                    {"level": g["prizeLevel"], "count": g["stakeCount"], "amount": g["stakeAmount"]}
                    for g in r.get("prizeLevelList", [])
                ],
            })
        return items
