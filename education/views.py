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
from uganda_common.utils import get_xform_dates, assign_backend
from .reports import attendance_stats, enrollment_stats, headteacher_attendance_stats, abuse_stats
from urllib2 import urlopen
from rapidsms_xforms.models import XFormSubmissionValue
# data
import datetime, re, time,xlwt
from datetime import datetime, date

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
def to_excel(req):

    default_style = xlwt.Style.default_style
    datetime_style = xlwt.easyxf(num_format_str='dd/mm/yyyy hh:mm')
    date_style = xlwt.easyxf(num_format_str='dd/mm/yyyy')

    data_models = [School, EmisReporter]

    book = xlwt.Workbook(encoding='utf8')

    #POSSIBLE DATASETS
    sheet_names = ["School",
        "Emis Reporters",
        "School and locations",
        "Emis Reporters and School count",
        "All poll data",
        "Vals submitted through polls",
        ]

    #TODO generalize writing function WIP
    def write_to_sheet(sheet_name=None,values_list=None):
        sheet = book.add_sheet(sheet_name)
        for row, rowdata in enumerate(values_list):
            for col, val in enumerate(rowdata):
                sheet.write(row,col,val)

    sheet0 = book.add_sheet(sheet_names[0])
    values_list0 = School.objects.all().values_list()
    for row, rowdata in enumerate(values_list0):
        for col, val in enumerate(rowdata):
            sheet0.write(row,col,val)


    sheet1 = book.add_sheet(sheet_names[1])
    values_list1 = EmisReporter.objects.all().values_list()
    for row, rowdata in enumerate(values_list1):
        for col, val in enumerate(rowdata):
            sheet1.write(row,col,val)

    # more specific data
    all_schools_list = School.objects.all() #objects

    # Schools and locations
    sheet2 = book.add_sheet(sheet_names[2])
    # format: (`school name` - `location`)
    data = [(s.name,s.location.name) for s in all_schools_list]
    for r, rd in enumerate(data):
        for c, v in enumerate(rd):
            sheet2.write(r,c,v)

    # EmisReporters and School count (usually by district or all generic locations.)
    sheet3 = book.add_sheet(sheet_names[3])
    all_emis_reporters = EmisReporter.objects.all()
    data = [(e.name,e.schools.values_list().count()) for e in all_emis_reporters]
    for r, rd in enumerate(data):
        for c, v in enumerate(rd):
            sheet3.write(r,c,v)

    # Locations and the number of schools in there
    sheet4 = book.add_sheet(sheet_names[4])
    submissions_from_polls = XFormSubmission.objects.all().values_list()
    for r, rd in enumerate(submissions_from_polls):
        for c, v in enumerate(rd):
            sheet4.write(r,c,v)

    # All posible values submitted by XForms
#    sheet5 = book.add_sheet(sheet_names[5])
#    submissions_values = XFormSubmissionValue.objects.all()
#    for r, rd in enumerate(submissions_values):
#        for c, v in enumerate(rd):
#            sheet5.write(r,c,v)
    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=emis.xls'
    book.save(response)
    return response