from django.db.signals import post_syncdb
from .utils import *

def parse_date(command, value):
    return 1

XFormField.register_field_type('emisdate', 'Date', parse_date,
                               db_type=XFormField.TYPE_INT, xforms_type='integer')

post_syncdb.connect(init_structures, weak=True)

