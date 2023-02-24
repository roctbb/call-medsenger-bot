from call_bot import *
from apscheduler.schedulers.background import BlockingScheduler
import tzlocal

scheduler = BlockingScheduler(timezone=str(tzlocal.get_localzone()))
scheduler.add_job(call_manager.iterate, 'interval', minutes=1, args=(app, ))
scheduler.add_job(call_manager.check_rooms, 'interval', minutes=5, args=(app, ))
scheduler.start()
