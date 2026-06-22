import logging
from datetime import datetime
import requests
from crawler.spiders.base import BaseSpider

logger = logging.getLogger(__name__)

API = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"


class SsqSpider(BaseSpider):
    lottery_code = "ssq"

    def fetch(self, issue_count=1):
        resp = requests.get(
            API, params={"name": "ssq", "issueCount": issue_count},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "http://www.cwl.gov.cn/"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def parse(self, raw):
        items = []
        for r in raw.get("result", []):
            try:
                reds = [int(x) for x in r["red"].split(",")]
                blues = [int(x) for x in r["blue"].split(",")]
                items.append({
                    "issue": r["code"],
                    "draw_date": datetime.strptime(r["date"][:10], "%Y-%m-%d").date(),
                    "numbers": {"red": reds, "blue": blues},
                    "sales_amount": str(r.get("sales", "")),
                    "pool_amount": str(r.get("poolmoney", "")),
                    "prize_grades": [
                        {"level": g["type"], "count": g["typenum"], "amount": g["typemoney"]}
                        for g in r.get("prizegrades", [])
                    ],
                })
            except Exception:
                logger.error(
                    "parse %s 记录解析失败, 跳过: %r",
                    self.lottery_code, r.get("code", r),
                    exc_info=True,
                )
                continue
        return items
