import sched
import time

from .deployment import utilization_per_deployment
from .utils import get_parser

parser = get_parser()
args = parser.parse_args()
kwargs = {key: value for key, value in args.__dict__.items()}
timelag = int(kwargs.pop("timelag"))


def repeat_task(scheduler):
    scheduler.enter(timelag, 1, repeat_task, (scheduler,))
    utilization_per_deployment(**kwargs)


utilization_per_deployment(**kwargs)
my_scheduler = sched.scheduler(time.time, time.sleep)
my_scheduler.enter(timelag, 1, repeat_task, (my_scheduler,))
my_scheduler.run()
