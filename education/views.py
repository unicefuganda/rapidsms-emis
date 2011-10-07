#from django.db import connection
from .forms import NewConnectionForm, DateRangeForm, EditReporterForm, DistrictFilterForm
from .models import *
from django.conf import settings, settings, settings
from django.contrib.auth.decorators import login_required, login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms.util import ErrorList
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404, render_to_response, \
    redirect, get_object_or_404, render_to_response
from django.template import RequestContext, RequestContext
from django.views.decorators.http import require_GET, require_POST, require_GET, \
    require_POST
from poll.models import Poll, ResponseCategory, Response
from rapidsms.models import Connection, Contact, Contact, Connection
from rapidsms_httprouter.models import Message
from uganda_common.utils import get_xform_dates, assign_backend
from .reports import attendance_stats, enrollment_stats, headteacher_attendance_stats, abuse_stats
from urllib2 import urlopen, urlopen
import datetime
import datetime
import re
import time

Num_REG = re.compile('\d+')

def index(request):
    return render_to_response("education/index.html", {}, RequestContext(request))

def dashboard(request):
    if request.user:
        return deo_dashboard(request)
    else:
        return index(request)

def deo_dashboard(request):
    form = DistrictFilterForm()
    district_id = None
    if request.method == 'POST':
        form = DistrictFilterForm(request.POST)
        if form.is_valid():
            district_id = form.cleaned_data['district']
    return render_to_response("education/deo_dashboard.html", {\
                                'form':form, \
                                'attendance_stats':attendance_stats(request, district_id), \
                                'enrollment_stats':enrollment_stats(request, district_id), \
                                'headteacher_attendance_stats':headteacher_attendance_stats(request, district_id), \
                                'abuse_stats':abuse_stats(request, district_id), \
                                }, RequestContext(request))

def whitelist(request):
    return render_to_response(
    "education/whitelist.txt",
    {'connections': Connection.objects.all()},
    mimetype="text/plain",
    context_instance=RequestContext(request))

def _reload_whitelists():
    refresh_urls = getattr(settings, 'REFRESH_WHITELIST_URL', None)
    if refresh_urls is not None:
        if not type(refresh_urls) == list:
            refresh_urls = [refresh_urls, ]
        for refresh_url in refresh_urls:
            try:
                status_code = urlopen(refresh_url).getcode()
                if int(status_code / 100) == 2:
                    continue
                else:
                    return False
            except Exception as e:
                return False
        return True
    return False

def _addto_autoreg(connections):
    for connection in connections:
        if not connection.contact and \
            not ScriptProgress.objects.filter(script__slug='emis_autoreg', connection=connection).count():
                        ScriptProgress.objects.create(script=Script.objects.get(slug="emis_autoreg"), \
                                              connection=connection)

@login_required
def add_connection(request):
    form = NewConnectionForm()
    if request.method == 'POST':
        form = NewConnectionForm(request.POST)
        connections = []
        if form.is_valid():
            identity = form.cleaned_data['identity']
            identity, backend = assign_backend(str(identity))
            connection, created = Connection.objects.get_or_create(identity=identity, backend=backend)
            connections.append(connection)
            other_numbers = request.POST.getlist('other_nums')
            if len(other_numbers) > 0:
                for number in other_numbers:
                    identity, backend = assign_backend(str(number))
                    connection, created = Connection.objects.get_or_create(identity=identity, backend=backend)
                    connections.append(connection)
            _addto_autoreg(connections)
            _reload_whitelists()
#            time.sleep(2)
            return render_to_response('education/partials/addnumbers_row.html', {'object':connections, 'selectable':False}, RequestContext(request))

    return render_to_response("education/partials/new_connection.html", {'form':form}, RequestContext(request))

@login_required
def delete_connection(request, connection_id):
    connection = get_object_or_404(Connection, pk=connection_id)
    connection.delete()
    _reload_whitelists()
    return render_to_response("education/partials/connection_view.html", {'object':connection.contact }, context_instance=RequestContext(request))

@login_required
def delete_reporter(request, reporter_pk):
    reporter = get_object_or_404(EmisReporter, pk=reporter_pk)
    if request.method == 'POST':
        reporter.delete()
    return HttpResponse(status=200)

@login_required
def edit_reporter(request, reporter_pk):
    reporter = get_object_or_404(EmisReporter, pk=reporter_pk)
    reporter_form = EditReporterForm(instance=reporter)
    if request.method == 'POST':
        reporter_form = EditReporterForm(instance=reporter,
                data=request.POST)
        if reporter_form.is_valid():
            reporter_form.save()
        else:
            return render_to_response('education/partials/edit_reporter.html'
                    , {'reporter_form': reporter_form, 'reporter'
                    : reporter},
                    context_instance=RequestContext(request))
        return render_to_response('/education/partials/reporter_row.html',
                                  {'object':Contact.objects.get(pk=reporter_pk),
                                   'selectable':True},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('education/partials/edit_reporter.html',
                                  {'reporter_form': reporter_form,
                                  'reporter': reporter},
                                  context_instance=RequestContext(request))
