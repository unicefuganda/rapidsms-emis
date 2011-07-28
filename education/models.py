from django.db.signals import post_syncdb
from .utils import *

def parse_date(command, value):
    return 1

XFormField.register_field_type('emisdate', 'Date', parse_date,
                               db_type=XFormField.TYPE_INT, xforms_type='integer')

post_syncdb.connect(init_structures, weak=True)
post_syncdb.connect(init_xforms, weak=True)
post_syncdb.connect(init_autoreg, weak=True)
post_syncdb.connect(init_scripts, weak=True)
