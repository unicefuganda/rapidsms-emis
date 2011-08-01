import rapidsms
import datetime

from rapidsms.apps.base import AppBase
from .models import Poll
from django.db.models import Q
from script.models import Script, ScriptProgress
from rapidsms.models import Contact

class App (AppBase):

    def handle (self, message):
        if not message.connection.contact and \
           not ScriptProgress.objects.filter(script__slug='emis_autoreg', connection=message.connection).count():
            ScriptProgress.objects.create(script=Script.objects.get(slug="emis_autoreg"), \
                                          connection=message.connection)
            return True
        return False
