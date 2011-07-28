from django.db.signals import post_syncdb
from .utils import *

post_syncdb.connect(init_structures, weak=True)
post_syncdb.connect(init_xforms, weak=True)
post_syncdb.connect(init_autoreg, weak=True)
post_syncdb.connect(init_scripts, weak=True)