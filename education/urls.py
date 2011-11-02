from .forms import SchoolFilterForm, LimitedDistictFilterForm, \
 RolesFilterForm, ReporterFreeSearchForm, SchoolDistictFilterForm, FreeSearchSchoolsForm
from .models import EmisReporter, School
from .reports import AttendanceReport, AbuseReport
from .sorters import LatestSubmissionSorter
from .views import whitelist, add_connection, delete_connection, deo_dashboard, dashboard, \
 edit_reporter, delete_reporter, add_schools, edit_school, delete_school, last_submission, to_excel, excel_reports
from contact.forms import FreeSearchForm, DistictFilterForm, MassTextForm, \
    FreeSearchTextForm, DistictFilterMessageForm, HandledByForm, ReplyTextForm
from django.conf.urls.defaults import patterns, url
from generic.sorters import SimpleSorter
from generic.views import generic, generic_row
from rapidsms_httprouter.models import Message
from rapidsms_xforms.models import XFormSubmission
from uganda_common.utils import get_xform_dates, get_messages
from django.contrib.auth.views import login_required


urlpatterns = patterns('',
   url(r'^emis/messagelog/$', generic, {
      'model':Message,
      'filter_forms':[FreeSearchTextForm, DistictFilterMessageForm, HandledByForm],
      'action_forms':[ReplyTextForm],
      'objects_per_page':25,
      'partial_row':'contact/partials/message_row.html',
      'base_template':'education/messages_base.html',
      'columns':[('Text', True, 'text', SimpleSorter()),
                 ('Contact Information', True, 'connection__contact__name', SimpleSorter(),),
                 ('Date', True, 'date', SimpleSorter(),),
                 ('Type', True, 'application', SimpleSorter(),),
                 ('Response', False, 'response', None,),
                 ],
      'sort_column':'date',
      'sort_ascending':False,
    }, name="emis-messagelog"),
   #reporters
    url(r'^emis/reporter/$', generic, {
      'model':EmisReporter,
      'filter_forms':[ReporterFreeSearchForm, RolesFilterForm, LimitedDistictFilterForm, SchoolFilterForm],
      'action_forms':[MassTextForm],
      'objects_per_page':25,
      'partial_row':'education/partials/reporter_row.html',
      'partial_header':'education/partials/reporter_partial_header.html',
      'base_template':'education/contacts_base.html',
      'results_title':'Reporters',
      'columns':[('Name', True, 'name', SimpleSorter()),
                 ('Number', True, 'connection__identity', SimpleSorter(),),
                 ('Role(s)', True, 'groups__name', SimpleSorter(),),
                 ('District', False, 'district', None,),
                 ('Last Reporting Date', True, 'latest_submission_date', LatestSubmissionSorter(),),
                 ('Total Reports', True, 'connection__submissions__count', SimpleSorter(),),
                 ('School(s)', True, 'schools__name', SimpleSorter(),),
#                 ('Location', True, 'reporting_location__name', SimpleSorter(),),
                 ('', False, '', None,)],
    }, name="emis-contact"),
    url(r'^emis/reporter/(\d+)/edit/', edit_reporter, name='edit-reporter'),
    url(r'^emis/reporter/(\d+)/delete/', delete_reporter, name='delete-reporter'),
    url(r'^emis/reporter/(?P<pk>\d+)/show', generic_row, {'model':EmisReporter, 'partial_row':'education/partials/reporter_row.html'}),
    url(r'^emis/attendance/$', generic, {
        'model':XFormSubmission,
        'queryset':AttendanceReport,
        'selectable':False,
        'paginated':False,
        'results_title':None,
        'top_columns':[
            ('', 1, None),
            ('student weekly attendance cutting', 4, None),
            ('teacher weekly attendance', 4, None),
        ],
        'columns':[
            ('', False, '', None),
            ('boys', False, 'boys', None),
            ('girls', False, 'girls', None),
            ('total', False, 'total_students', None),
#            ('% student attendance', False, 'percentage_students', None),
            ('% absent', False, 'percentange_student_absentism', None),
            ('males', False, 'male_teachers', None),
            ('females', False, 'female_teachers', None),
            ('total', False, 'total_teachers', None),
#            ('% of deployed', False, 'percentage_teacher', None),
            ('% absent', False, 'percentange_teachers_absentism', None),
        ],
        'partial_row':'education/partials/school_report_row.html',
        'partial_header':'education/partials/attendance_partial_header.html',
        'base_template':'generic/timeslider_base.html',
        'needs_date':True,
        'dates':get_xform_dates,
    }, name='attendance-stats'),

    url(r'^$', dashboard, name='rapidsms-dashboard'),
    url(r'^emis/whitelist/', whitelist),
    url(r'^connections/add/', add_connection),
    url(r'^connections/(\d+)/delete/', delete_connection),

    url(r'^emis/deo_dashboard/', login_required(deo_dashboard), {}, name='deo-dashboard'),
    url(r'^emis/school/$', generic, {
      'model':School,
      'filter_forms':[FreeSearchSchoolsForm, SchoolDistictFilterForm],
      'objects_per_page':25,
      'partial_row':'education/partials/school_row.html',
      'partial_header':'education/partials/school_partial_header.html',
      'base_template':'education/schools_base.html',
      'columns':[('Name', True, 'name', SimpleSorter()),
                 ('District', True, 'location__name', None,),
                 ('School ID', False, 'emis_id', None,),
                 ('Reporters', False, 'emisreporter', None,),
                 ],
      'sort_column':'date',
      'sort_ascending':False,
    }, name="emis-schools"),
    url(r'^emis/(\d+)/last_submission/', last_submission, {}, name='last-submission'),
    url(r'^emis/add_schools/', login_required(add_schools), {}, name='add-schools'),
    url(r'^emis/school/(\d+)/edit/', edit_school, name='edit-school'),
    url(r'^emis/school/(\d+)/delete/', delete_school, name='delete-school'),
    url(r'^emis/school/(?P<pk>\d+)/show', generic_row, {'model':School, 'partial_row':'education/partials/school_row.html'}, name='show-school'),

    url(r'^emis/othermessages/$', generic, {
      'model':Message,
      'queryset':get_messages,
      'filter_forms':[FreeSearchTextForm, DistictFilterMessageForm, HandledByForm],
      'action_forms':[ReplyTextForm],
      'objects_per_page':25,
      'partial_row':'education/partials/other_message_row.html',
      'base_template':'education/messages_base.html',
      'columns':[('Text', True, 'text', SimpleSorter()),
                 ('Contact Information', True, 'connection__contact__name', SimpleSorter(),),
                 ('Date', True, 'date', SimpleSorter(),),
                 ],
      'sort_column':'date',
      'sort_ascending':False,
    }, name="emis-othermessages"),

    url(r'^emis/abuse/$', generic, {
        'model':XFormSubmission,
        'queryset':AbuseReport,
        'selectable':False,
        'paginated':False,
        'results_title':None,
        'columns':[
            ('', False, '', None),
            ('total cases', False, 'total_cases', None),
        ],
        'partial_row':'education/partials/abuse_report_row.html',
        'partial_header':'education/partials/partial_header.html',
        'base_template':'generic/timeslider_base.html',
        'needs_date':True,
        'dates':get_xform_dates,
    }, name='abuse-stats'),

    # excel
    url(r'^emis/excelreports/$',excel_reports),
    url(r'^emis/toexcel/$',to_excel),
)
