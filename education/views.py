#from django.db import connection
from .forms import NewConnectionForm, EditReporterForm, DistrictFilterForm, SchoolForm
from .models import *
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from poll.models import Poll, ResponseCategory, Response
from rapidsms.models import Connection, Contact, Contact, Connection
from rapidsms_httprouter.models import Message
from rapidsms.contrib.locations.models import Location
from uganda_common.utils import *

from .reports import *
from .utils import *
from urllib2 import urlopen
from rapidsms_xforms.models import XFormSubmissionValue
import datetime, re, time
from datetime import datetime, date

Num_REG = re.compile('\d+')

def index(request):
    return render_to_response("education/index.html", {}, RequestContext(request))

@login_required
def dashboard(request):
    profile = request.user.get_profile()
    if profile.is_member_of('DEO'):
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
    user_location = Location.objects.get(pk=district_id) if district_id else get_location_for_user(request.user)
    if user_location == Location.tree.root_nodes()[0]:
        user_location = Location.objects.get(name='Kaabong')
    return render_to_response("education/deo/deo_dashboard.html", {\
                                'location':user_location,\
                                'form':form, \
                                'keyratios':keyratios_stats(request, district_id),\
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
            identity, backend = assign_backend(str(identity.strip()))
            connection, created = Connection.objects.get_or_create(identity=identity, backend=backend)
            connections.append(connection)
            other_numbers = request.POST.getlist('other_nums')
            if len(other_numbers) > 0:
                for number in other_numbers:
                    identity, backend = assign_backend(str(number.strip()))
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
                                  {'object':EmisReporter.objects.get(pk=reporter_pk),
                                   'selectable':True},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('education/partials/edit_reporter.html',
                                  {'reporter_form': reporter_form,
                                  'reporter': reporter},
                                  context_instance=RequestContext(request))

@login_required
def add_schools(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        schools = []
        if form.is_valid():
            names = filter(None, request.POST.getlist('name'))
            locations = request.POST.getlist('location')
            emis_ids = request.POST.getlist('emis_id')
            if len(names) > 0:
                for i, name in enumerate(names):
                    location = Location.objects.get(pk=int(locations[i]))
                    emis_id = emis_ids[i]
                    name, created = School.objects.get_or_create(name=name, location=location, emis_id=emis_id)
                    schools.append(name)

                return render_to_response('education/partials/addschools_row.html', {'object':schools, 'selectable':False}, RequestContext(request))
    else:
        form = SchoolForm()
    return render_to_response('education/deo/add_schools.html',
                                  {'form': form,
                                }, context_instance=RequestContext(request))

@login_required
def delete_school(request, school_pk):
    school = get_object_or_404(School, pk=school_pk)
    if request.method == 'POST':
        school.delete()
    return HttpResponse(status=200)

@login_required
def edit_school(request, school_pk):
    school = get_object_or_404(School, pk=school_pk)
    school_form = SchoolForm(instance=school)
    if request.method == 'POST':
        school_form = SchoolForm(instance=school,
                data=request.POST)
        if school_form.is_valid():
            school_form.save()
        else:
            return render_to_response('education/partials/edit_school.html'
                    , {'school_form': school_form, 'school'
                    : school},
                    context_instance=RequestContext(request))
        return render_to_response('/education/partials/school_row.html',
                                  {'object':School.objects.get(pk=school_pk),
                                   'selectable':True},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('education/partials/edit_school.html',
                                  {'school_form': school_form,
                                  'school': school},
                                  context_instance=RequestContext(request))
        
@login_required
def school_detail(request, school_id):
    school = School.objects.get(id=school_id)
    last_submissions = school_last_xformsubmission(request, school_id)
    return render_to_response("education/school_detail.html", {\
                            'school': school,
                            'last_submissions': last_submissions,
                                }, RequestContext(request))


# analytics specific for emis {copy, but adjust to suit your needs}
@login_required
def to_excel(req,district_id=None):
    return create_excel_dataset()

@login_required
def excel_reports(req):
    #all dicts
    head_teacher_res =headteacher_attendance_stats(req)
    attendance_res = attendance_stats(req)
    enrollment_res = enrollment_stats(req)
    abuse_res = abuse_stats(req)
    return render_to_response('education/excelreports/excel_dashboard.html',{"res":head_teacher_res,"en":enrollment_res},RequestContext(req))
