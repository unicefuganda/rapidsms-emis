"""
Basic tests for CVS
"""

from django.test import TestCase
from django.contrib.auth.models import User, Group
from rapidsms.messages.incoming import IncomingMessage
from rapidsms_xforms.models import *
from cvs.utils import init_xforms
from healthmodels.models import *
from rapidsms_httprouter.models import Message
from rapidsms.contrib.locations.models import Location, LocationType
import datetime
from rapidsms.models import Connection, Backend, Contact
from rapidsms.messages.incoming import IncomingMessage
from rapidsms_xforms.models import XForm
from django.conf import settings
from script.utils.outgoing import check_progress
from script.models import Script, ScriptProgress, ScriptSession, ScriptResponse
from education.utils import *
from rapidsms_httprouter.router import get_router
from script.signals import script_progress_was_completed, script_progress
from poll.utils import create_attributes
from .models import EmisReporter, School


class ModelTest(TestCase): #pragma: no cover

    def fake_incoming(self, message, connection=None):
        if connection is None:
            connection = self.connection
        router = get_router()
        router.handle_incoming(connection.backend.name, connection.identity, message)


    def spoof_incoming_obj(self, message, connection=None):
        if connection is None:
            connection = Connection.objects.all()[0]
        incomingmessage = IncomingMessage(connection, message)
        incomingmessage.db_message = Message.objects.create(direction='I', connection=Connection.objects.all()[0], text=message)
        return incomingmessage


    def assertResponseEquals(self, message, expected_response, connection=None):
        s = self.fake_incoming(message, connection)
        self.assertEquals(s.response, expected_response)


    def fake_submission(message, connection=None):
        form = XForm.find_form(message)
        if connection is None:
            try:
                connection = Connection.objects.all()[0]
            except IndexError:
                backend, created = Backend.objects.get_or_create(name='test')
                connection, created = Connection.objects.get_or_create(identity='8675309',
                                                                       backend=backend)
        # if so, process it
        incomingmessage = IncomingMessage(connection, message)
        incomingmessage.db_message = Message.objects.create(direction='I', connection=connection, text=message)
        if form:
            submission = form.process_sms_submission(incomingmessage)
            return submission
        return None


    def fake_error_submission(self, message, connection=None):
        form = XForm.find_form(message)

        if connection is None:
            connection = Connection.objects.all()[0]
        # if so, process it
        incomingmessage = IncomingMessage(connection, message)
        incomingmessage.db_message = Message.objects.create(direction='I', connection=Connection.objects.all()[0], text=message)
        if form:
            submission = form.process_sms_submission(incomingmessage)
            self.failUnless(submission.has_errors)
        return


    def setUp(self):
        if 'django.contrib.sites' in settings.INSTALLED_APPS:
            site_id = getattr(settings, 'SITE_ID', 1)
            Site.objects.get_or_create(pk=site_id, defaults={'domain':'rapidemis.com'})
        init_groups()
        init_xforms(None)
        init_autoreg(None)
        init_scripts(None)
        create_attributes()
        User.objects.get_or_create(username='admin')
        self.backend = Backend.objects.create(name='test')
        self.connection = Connection.objects.create(identity='8675309', backend=self.backend)
        country = LocationType.objects.create(name='country', slug='country')
        district = LocationType.objects.create(name='district', slug='district')
        subcounty = LocationType.objects.create(name='sub_county', slug='sub_county')
        self.root_node = Location.objects.create(type=country, name='Uganda')
        self.kampala_district = Location.objects.create(type=district, name='Kampala')
        self.kampala_subcounty = Location.objects.create(type=subcounty, name='Kampala')
        self.gulu_subcounty = Location.objects.create(type=subcounty, name='Gulu')
        self.gulu_school = School.objects.create(name="St. Mary's", location=self.gulu_subcounty)
        self.kampala_school = School.objects.create(name="St. Mary's", location=self.kampala_subcounty)


    def fake_script_dialog(self, script_prog, connection, responses, emit_signal=True):
        script = script_prog.script
        ss = ScriptSession.objects.create(script=script, connection=connection, start_time=datetime.datetime.now())
        for poll_name, resp in responses:
            poll = script.steps.get(poll__name=poll_name).poll
            poll.process_response(self.spoof_incoming_obj(resp))
            resp = poll.responses.all()[0]
            ScriptResponse.objects.create(session=ss, response=resp)
        if emit_signal:
            script_progress_was_completed.send(connection=connection, sender=script_prog)
        return ss

    def testBasicAutoReg(self):
        self.fake_incoming('join')
        self.assertEquals(ScriptProgress.objects.count(), 1)
        script_prog = ScriptProgress.objects.all()[0]
        self.assertEquals(script_prog.script.slug, 'emis_autoreg')

        self.fake_script_dialog(script_prog, self.connection, [\
            ('emis_role', 'teacher'), \
            ('emis_district', 'kampala'), \
            ('emis_subcounty', 'kampala'), \
            ('emis_one_school', 'st. marys'), \
            ('emis_name', 'testy mctesterton'), \
        ])
        self.assertEquals(EmisReporter.objects.count(), 1)
        contact = EmisReporter.objects.all()[0]
        self.assertEquals(contact.name, 'Testy Mctesterton')
        self.assertEquals(contact.reporting_location, self.kampala_subcounty)
        self.assertEquals(contact.school, self.kampala_school)
        self.assertEquals(contact.groups.all()[0].name, 'Teachers')

    def testBadAutoReg(self):
        """
        Crummy answers
        """
        self.fake_incoming('join')
        script_prog = ScriptProgress.objects.all()[0]
        self.fake_script_dialog(script_prog, self.connection, [\
            ('emis_role', 'bodaboda'), \
            ('emis_district', 'kampala'), \
            ('emis_subcounty', 'amudat'), \
            ('emis_name', 'bad tester'), \
        ])
        self.assertEquals(EmisReporter.objects.count(), 1)
        contact = EmisReporter.objects.all()[0]
        self.assertEquals(contact.groups.all()[0].name, 'Other EMIS Reporters')
        self.assertEquals(contact.reporting_location, self.kampala_district)

    def testAutoRegNoLocationData(self):

        self.fake_incoming('join')
        script_prog = ScriptProgress.objects.all()[0]
        self.fake_script_dialog(script_prog, self.connection, [\
            ('emis_role', 'teacher'), \
            ('emis_name', 'no location data tester'), \
        ])
        self.assertEquals(EmisReporter.objects.count(), 1)
        contact = EmisReporter.objects.all()[0]
        self.assertEquals(contact.reporting_location, self.root_node)

    def testAutoRegNoRoleNoName(self):
        self.fake_incoming('join')
        script_prog = ScriptProgress.objects.all()[0]
        self.fake_script_dialog(script_prog, self.connection, [\
            ('emis_district', 'kampala'), \
            ('emis_subcounty', 'Gul'), \
            ('emis_one_school', 'St Marys'), \
        ])
        contact = EmisReporter.objects.all()[0]
        self.assertEquals(contact.groups.all()[0].name, 'Other EMIS Reporters')
        self.assertEquals(contact.reporting_location, self.gulu_subcounty)
        self.assertEquals(contact.name, 'Anonymous User')


    def assertScriptSkips(self, connection, role, initial_question, final_question):
        connection = Connection.objects.create(identity=connection, backend=self.backend)
        script = Script.objects.get(slug='emis_autoreg')
        script_prog = ScriptProgress.objects.create(script=script, connection=connection, step=script.steps.get(poll__name=initial_question), status='C', num_tries=1)
        script_prog.set_time(datetime.datetime.now() - datetime.timedelta(1))
        self.fake_script_dialog(script_prog, connection, [\
            ('emis_role', role)
        ], emit_signal=False)
        check_progress(connection)
        script_prog = ScriptProgress.objects.get(connection=connection)
        self.assertEquals(script_prog.step.poll.name, final_question)


    def testAutoRegTransitions(self):
        self.assertScriptSkips('8675310', 'deo', 'emis_district', 'emis_name')
        self.assertScriptSkips('8675311', 'cct', 'emis_district', 'emis_name')
        self.assertScriptSkips('8675312', 'district officials', 'emis_district', 'emis_name')

        self.assertScriptSkips('8675313', 'gem', 'emis_district', 'emis_subcounty')
        self.assertScriptSkips('8675314', 'smc', 'emis_district', 'emis_subcounty')
        self.assertScriptSkips('8675315', 'head teachers', 'emis_district', 'emis_subcounty')
        self.assertScriptSkips('8675316', 'teachers', 'emis_district', 'emis_subcounty')

        self.assertScriptSkips('8675317', 'gem', 'emis_subcounty', 'emis_many_school')

        self.assertScriptSkips('8675318', 'teachers', 'emis_subcounty', 'emis_one_school')
        self.assertScriptSkips('8675319', 'head teachers', 'emis_subcounty', 'emis_one_school')
        self.assertScriptSkips('8675320', 'smc', 'emis_subcounty', 'emis_one_school')


    def assertXFormAdvancedScript(self, message, completed_step, advance=True):
        self.fake_incoming(message)
        script_prog = ScriptProgress.objects.all()[0]
        self.assertEquals(script_prog.step.order, completed_step)
        self.assertEquals(script_prog.status, 'C')
        # advance to next step
        if advance:
            script_prog.step = script_prog.script.steps.get(order=completed_step + 1)
            script_prog.status = 'P'
            script_prog.save()

    def testOtherScriptHandlers(self):
        # fake that this connection has already gone through autoreg
        contact = Contact.objects.create(name='Testy McTesterton')
        self.connection.contact = contact
        self.connection.save()

        script = Script.objects.get(slug='emis_annual')
        script_prog = ScriptProgress.objects.create(script=script, connection=self.connection, step=script.steps.get(order=0), status='P')

        self.assertXFormAdvancedScript('classrooms 2 2 3 3 4 4 5', 0)
        self.assertXFormAdvancedScript('classroomsused 2 2 3 3 4 4 5', 1)
        self.assertXFormAdvancedScript('latrines g 20 b 26 f 7 m 9', 2)
        self.assertXFormAdvancedScript('latrinesused g 20 b 26 f 7 m 9', 3)
        self.assertXFormAdvancedScript('deploy f 2 m 4', 4)
        self.assertXFormAdvancedScript('enrolledb 200 200 30 45 89 90 23', 5)
        self.assertXFormAdvancedScript('enrolledg 300 120 80 67 43 12 5', 6, False)

