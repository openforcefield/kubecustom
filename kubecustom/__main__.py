import sched
import time
import warnings

from .deployment import utilization_per_deployment
from .utils import get_parser, repeat_task

parser = get_parser()
args = parser.parse_args()
kwargs = {key: value for key, value in args.__dict__.items()}
timelag = int(kwargs.pop("timelag"))

silence = kwargs.pop("silence")
if silence:
    warnings.filterwarnings("ignore")

utilization_per_deployment(**kwargs)
my_scheduler = sched.scheduler(time.time, time.sleep)
my_scheduler.enter(
    timelag, 1, repeat_task, (my_scheduler, utilization_per_deployment, kwargs, timelag)
)
my_scheduler.run()
