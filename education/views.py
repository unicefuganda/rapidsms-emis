#from django.db import connection
from .forms import NewConnectionForm, EditReporterForm, DistrictFilterForm, SchoolForm
from .models import *
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from poll.models import Poll, ResponseCategory, Response
from rapidsms.models import Connection, Contact, Contact, Connection
from rapidsms_httprouter.models import Message
from uganda_common.utils import *
from rapidsms.contrib.locations.models import Location

# reusing reports methods
from education.reports import *
from urllib2 import urlopen
from rapidsms_xforms.models import XFormSubmissionValue
# data
import datetime, re, time,xlwt
from datetime import datetime, date

Num_REG = re.compile('\d+')

def index(request):
    return render_to_response("education/index.html", {}, RequestContext(request))

@login_required
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
    return render_to_response("education/deo/deo_dashboard.html", {\
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
def last_submission(request, school_id):
    school = School.objects.get(id=school_id)
    xforms = XForm.objects.all()
    return render_to_response("education/last_school_submission.html", {\
                            'school': school,
                            'xforms': xforms,
                                }, RequestContext(request))


# analytics specific for emis {copy, but adjust to suit your needs}
@login_required
def to_excel(req):
#    stats = []
    #this can be expanded for other districts
    CURRENT_DISTRICTS_UNDER_EMIS = ["Kaabong",
                                    "Kotido",
                                    "Kabarole",
                                    "Kisoro",
                                    "Kyegegwa",
                                    "Mpigi",
                                    "Kabale"
                                    ]


    user_locations_by_district = [Location.objects.get(name=l) for l in CURRENT_DISTRICTS_UNDER_EMIS]
    location = Location.tree.root_nodes()[0]
    start_date, end_date = previous_calendar_week()
    dates = {'start':start_date, 'end':end_date}
    loc_data = []
    res = {}
    for loc in CURRENT_DISTRICTS_UNDER_EMIS:
        user_location = Location.objects.get(name=loc)
        stats = []

        boys = ["boys_%s" % g for g in GRADES]
        values = total_attribute_value(boys, start_date=start_date, end_date=end_date, location=location)
        stats.append(('boys', location_values(user_location, values)))

        girls = ["girls_%s" % g for g in GRADES]
        values = total_attribute_value(girls, start_date=start_date, end_date=end_date, location=location)
        stats.append(('girls', location_values(user_location, values)))

        total_pupils = ["boys_%s" % g for g in GRADES] + ["girls_%s" % g for g in GRADES]
        values = total_attribute_value(total_pupils, start_date=start_date, end_date=end_date, location=location)
        stats.append(('total pupils', location_values(user_location, values)))

        values = total_attribute_value("teachers_f", start_date=start_date, end_date=end_date, location=location)
        stats.append(('female teachers', location_values(user_location, values)))

        values = total_attribute_value("teachers_m", start_date=start_date, end_date=end_date, location=location)
        stats.append(('male teachers', location_values(user_location, values)))

        values = total_attribute_value(["teachers_f", "teachers_m"], start_date=start_date, end_date=end_date, location=location)
        stats.append(('total teachers', location_values(user_location, values)))
        loc_data.append(stats)

    book = xlwt.Workbook(encoding='utf8')
    sheet = book.add_sheet('attendance')
    # data in loc_data is organized by district, every new list element is a district under EMIS
    for row in xrange(len(loc_data)):
        for col,col_data in enumerate(loc_data[row]):
            sheet.write(row,col,col_data[1])

    loc_data = []
    for loc in CURRENT_DISTRICTS_UNDER_EMIS:
        user_location = Location.objects.get(name=loc)
        stats = []

        boys = ["enrolledb_%s" % g for g in GRADES]
        values = total_attribute_value(boys, start_date=start_date, end_date=end_date, location=location)
        stats.append(('boys', location_values(user_location, values)))

        girls = ["enrolledg_%s" % g for g in GRADES]
        values = total_attribute_value(girls, start_date=start_date, end_date=end_date, location=location)
        stats.append(('girls', location_values(user_location, values)))

        total_pupils = ["enrolledb_%s" % g for g in GRADES] + ["enrolledg_%s" % g for g in GRADES]
        values = total_attribute_value(total_pupils, start_date=start_date, end_date=end_date, location=location)
        stats.append(('total pupils', location_values(user_location, values)))

        values = total_attribute_value("deploy_f", start_date=start_date, end_date=end_date, location=location)
        stats.append(('female teachers', location_values(user_location, values)))

        values = total_attribute_value("deploy_m", start_date=start_date, end_date=end_date, location=location)
        stats.append(('male teachers', location_values(user_location, values)))

        values = total_attribute_value(["deploy_f", "deploy_m"], start_date=start_date, end_date=end_date, location=location)
        stats.append(('total teachers', location_values(user_location, values)))
        loc_data.append(stats)
    #TODO refactor code and get rid of duplication
    sheet2 = book.add_sheet('enrolment')
    for row in xrange(len(loc_data)):
       for col,col_data in enumerate(loc_data[row]):
           sheet2.write(row,col,col_data[1])

    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=emis.xls'
    book.save(response)
    return response

@login_required
def excel_reports(req):
    return render_to_response('education/excelreports/excel_dashboard.html',{},RequestContext(req))
