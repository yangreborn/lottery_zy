import logging
from django.core.management.base import BaseCommand
import django_rq
from crawler.schedule import dispatch_due_polls

logger = logging.getLogger(__name__)

JOB_ID = "crawler.dispatch_due_polls"


class Command(BaseCommand):
    help = "注册 rq-scheduler 每分钟巡检任务(幂等)。部署/更新后运行一次。"

    def handle(self, *args, **options):
        scheduler = django_rq.get_scheduler("default")
        # 先清理旧的巡检任务，避免重复叠加(幂等)
        for job in scheduler.get_jobs():
            if job.id == JOB_ID or (job.func_name or "").endswith("dispatch_due_polls"):
                scheduler.cancel(job)
                logger.info("清理旧巡检任务 %s", job.id)
        scheduler.cron(
            "* * * * *",
            func=dispatch_due_polls,
            id=JOB_ID,
            queue_name="default",
        )
        logger.info("已注册每分钟巡检任务 %s", JOB_ID)
        self.stdout.write("已注册每分钟开奖巡检任务 dispatch_due_polls")
