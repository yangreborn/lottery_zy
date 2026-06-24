import logging
from datetime import datetime
import requests
from crawler.spiders.base import BaseSpider

logger = logging.getLogger(__name__)

API = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"


class KL8Spider(BaseSpider):
    lottery_code = "kl8"

    def fetch(self, issue_count=1):
        resp = requests.get(
            API, params={"name": "kl8", "issueCount": issue_count},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "http://www.cwl.gov.cn/"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def parse(self, raw):
        items = []
        for r in raw.get("result", []):
            try:
                mains = [int(x) for x in r["red"].split(",")]
                items.append({
                    "issue": r["code"],
                    "draw_date": datetime.strptime(r["date"][:10], "%Y-%m-%d").date(),
                    "numbers": {"main": mains},
                    "sales_amount": str(r.get("sales", "")),
                    "pool_amount": str(r.get("poolmoney", "")),
                    "prize_grades": [
                        {"level": g["type"], "count": g["typenum"], "amount": g["typemoney"]}
                        for g in r.get("prizegrades", [])
                    ],
                })
            except Exception:
                logger.error("parse kl8 记录解析失败, 跳过: %r", r.get("code", r), exc_info=True)
                continue
        return items
