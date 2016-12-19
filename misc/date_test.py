from pytz import timezone
import pytz
utc = pytz.utc
print utc.zone

eastern = timezone('US/Eastern')
print eastern.zone

amsterdam = timezone('Europe/Amsterdam')
fmt = '%Y-%m-%d %H:%M:%S %Z%z'