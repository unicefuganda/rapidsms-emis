'''
Created on Sep 15, 2011

@author: asseym
'''
from script.utils.handling import find_best_response
from script.models import Script, ScriptSession, ScriptProgress
from .models import EmisReporter, _schedule_monthly_script
from rapidsms.models import Connection
from datetime import datetime,date

from contact.models import MessageFlag
from rapidsms.models import Contact
from poll.models import Poll
from script.models import ScriptStep
from django.db.models import Count


def match_connections():
    script = Script.objects.get(slug='emis_autoreg')
    name_poll = script.steps.get(order=6).poll
    for connection in Connection.objects.all():
        try:
            session = ScriptSession.objects.filter(script=script, connection=connection).order_by('-end_time')[0]
        except IndexError:
            print 'Session for ' + connection.identity + ' does not exist!'
            continue
        try:
            name = find_best_response(session, name_poll)
        except AttributeError:
            import pdb;pdb.set_trace()
            find_best_response(session, name_poll)
        if name:
            name = ' '.join([n.capitalize() for n in name.lower().split(' ')])
            try:
                contact = EmisReporter.objects.get(name=name[:100])
                connection.contact = contact
                connection.save()
            except EmisReporter.MultipleObjectsReturned:
                print name[:100] + ' registered more than once!'
            except EmisReporter.DoesNotExist:
                print name[:100] + ' with connection ' + connection.identity + ' does not exist'

    #    connections = Connection.objects.filter(identity__in=['256774611460','256772544169','256772858848','256700601485','256777092848','256772966162','256782505870','256778301798'])
    #    for connection in connections:
    #        connection.contact = None
    #        connection.save()


def get_contacts(**kwargs):
    request = kwargs.pop('request')
    if request.user.is_authenticated() and hasattr(Contact, 'groups'):
        return Contact.objects.filter(groups__in=request.user.groups.all()).distinct().annotate(Count('responses'))
    else:
        return Contact.objects.annotate(Count('responses'))

def get_polls(**kwargs):
    script_polls = ScriptStep.objects.exclude(poll=None).values_list('poll', flat=True)
    return Poll.objects.exclude(pk__in=script_polls).annotate(Count('responses'))

def get_script_polls(**kwargs):
    script_polls = ScriptStep.objects.exclude(poll=None).values_list('poll', flat=True)
    return Poll.objects.filter(pk__in=script_polls).annotate(Count('responses'))

#def retrieve_poll(request):
#    pks=request.GET.get('pks', '').split('+')
#    if pks[0] == 'l':
#        return [Poll.objects.latest('start_date')]
#    else:
#        pks=[eval(x) for x in list(str(pks[0]).rsplit())]
#        return Poll.objects.filter(pk__in=pks)

def retrieve_poll(request, pks=None):
    script_polls = ScriptStep.objects.exclude(poll=None).values_list('poll', flat=True)
    if pks == None:
        pks = request.GET.get('pks', '')
    if pks == 'l':
        return [Poll.objects.exclude(pk__in=script_polls).latest('start_date')]
    else:
        return Poll.objects.filter(pk__in=[pks]).exclude(pk__in=script_polls)

def get_flagged_messages(**kwargs):

    return MessageFlag.objects.all()

# a manual reschedule of all monthly polls
def reschedule_monthly_polls():
    slugs = ['emis_abuse', 'emis_meals', 'emis_school_administrative', 'emis_smc_monthly']
    for slug in slugs:
        reporters = EmisReporter.objects.all()
        for reporter in reporters:
            if reporter.default_connection and reporter.groups.count() > 0:
                connection = reporter.default_connection
                group = reporter.groups.all()[0]
                if slug == 'emis_abuse':
                    _schedule_monthly_script(group, connection, 'emis_abuse', 'last', ['Teachers', 'Head Teachers'])
                elif slug == 'emis_meals':
                    _schedule_monthly_script(group, connection, 'emis_meals', 20, ['Teachers', 'Head Teachers'])
                elif slug == 'emis_school_administrative':
                    _schedule_monthly_script(group, connection, 'emis_school_administrative', 15, ['Teachers', 'Head Teachers'])
                else:
                    _schedule_monthly_script(group, connection, 'emis_smc_monthly', 28, ['SMC'])

#reschedule weekly SMS questions                
def reschedule_weekly_smc_polls():
    smcs = EmisReporter.objects.filter(groups__name='SMC')
    import datetime
    for smc in smcs:
        connection = smc.default_connection
        holidays = getattr(settings, 'SCHOOL_HOLIDAYS', [])
        d = datetime.datetime.now()
        # get the date to a thursday
        d = d + datetime.timedelta((3 - d.weekday()) % 7)
        in_holiday = True
        while in_holiday:
            in_holiday = False
            for start, end in holidays:
                if d >= start and d <= end:
                    in_holiday = True
                    break
            if in_holiday:
                d = d + datetime.timedelta(7)
        sp, created = ScriptProgress.objects.get_or_create(connection=connection, script=Script.objects.get(slug='emis_head_teacher_presence'))
        sp.set_time(d) 

