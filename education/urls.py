from .forms import SchoolFilterForm
from .models import EmisReporter
from .reports import MainEmisReport, ClassRoomReport, DashBoardReport, AttendanceReport, HtAttendanceReport, EnrollmentReport, AbuseReport
from .sorters import LatestSubmissionSorter
from .views import whitelist, add_connection, delete_connection
from contact.forms import FreeSearchForm, DistictFilterForm, MassTextForm, \
    FreeSearchTextForm, DistictFilterMessageForm, HandledByForm, ReplyTextForm
from django.conf.urls.defaults import patterns, url
from generic.sorters import SimpleSorter
from generic.views import generic
from rapidsms_httprouter.models import Message
from rapidsms_xforms.models import XFormSubmission
from uganda_common.utils import get_xform_dates

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
      'filter_forms':[FreeSearchForm, DistictFilterForm, SchoolFilterForm],
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
                 ('School', True, 'school__name', SimpleSorter(),),
                 ('Location', True, 'location__name', SimpleSorter(),),
                 ('', False, '', None,)],
    }, name="emis-contact"),
    url(r'^emis/stats/$', generic, {
        'model':XFormSubmission,
        'queryset':MainEmisReport,
        'selectable':False,
        'paginated':False,
        'results_title':None,
        'top_columns':[
            ('', 1, None),
            ('P3', 2, None),
            ('P5', 2, None),
            ('Teachers', 2, None),
            ('Abuse', 1, None),
            ('Classrooms', 1, '/emis/stats/classroom/'),

        ],
        'columns':[
            ('', False, '', None),
            ('boys attendance', False, '', None),
            ('girls attendance', False, '', None),
            ('boys attendance', False, '', None),
            ('girls attendance', False, '', None),
            ('males deployed', False, '', None),
            ('females deployed', False, '', None),
            ('reported incidents', False, '', None),
            ('total for p4', False, '', None),
        ],
        'partial_row':'education/partials/report_row.html',
        'partial_header':'education/partials/partial_header.html',
        'base_template':'generic/timeslider_base.html',
        'needs_date':True,
        'dates':get_xform_dates,
    }, name='stats'),

    url(r'^emis/stats/classroom/$', generic, {
        'model':XFormSubmission,
        'queryset':ClassRoomReport,
        'selectable':False,
        'paginated':False,
        'results_title':None,
        'top_columns':[
            ('', 1, None),
            ('P1', 2, None),
            ('P2', 2, None),
            ('P3', 2, None),
            ('P4', 2, None),
            ('P5', 2, None),
            ('P6', 2, None),
            ('P7', 2, None),
        ],
        'columns':[
            ('', False, '', None),
            ('total', False, '', None),
            ('used', False, '', None),
            ('total', False, '', None),
            ('used', False, '', None),
            ('total', False, '', None),
            ('used', False, '', None),
            ('total', False, '', None),
            ('used', False, '', None),
            ('total', False, '', None),
            ('used', False, '', None),
            ('total', False, '', None),
            ('used', False, '', None),
            ('total', False, '', None),
            ('used', False, '', None),
        ],
        'partial_row':'education/partials/report_row.html',
        'partial_header':'education/partials/partial_header.html',
        'base_template':'generic/timeslider_base.html',
        'needs_date':True,
        'dates':get_xform_dates,
    }),
    url(r'^$', generic, {
        'model':XFormSubmission,
        'queryset':DashBoardReport,
        'selectable':False,
        'paginated':False,
        'results_title':None,
        'columns':[
            ('', False, '', None),
            ('pupil attendance', False, '', None),
            ('teacher attendance', False, '', None),
            ('total enrollment', False, '', None),
            ('teacher deployment', False, '', None),
            ('abuse cases', False, '', None),
        ],
        'partial_row':'education/partials/report_row.html',
        'partial_header':'education/partials/partial_header.html',
        'base_template':'generic/timeslider_base.html',
        'needs_date':True,
        'dates':get_xform_dates,
    }, name='rapidsms-dashboard'),
    url(r'^emis/whitelist/', whitelist),
    url(r'^connections/add/', add_connection),
    url(r'^connections/(\d+)/delete/', delete_connection),

    url(r'^emis/deo_dashboard/', generic, {
        'model':XFormSubmission,
        'queryset':DashBoardReport,
        'selectable':False,
        'paginated':False,
        'results_title':None,
        'columns':[
            ('', False, '', None),
            ('pupil attendance', False, '', None),
            ('teacher attendance', False, '', None),
            ('total enrollment', False, '', None),
            ('teacher deployment', False, '', None),
            ('abuse cases', False, '', None),
        ],
        'partial_row':'education/partials/report_row.html',
        'partial_header':'education/partials/partial_header.html',
        'base_template':'generic/timeslider_base.html',
        'needs_date':True,
        'dates':get_xform_dates,
    }, name='deo-dashboard'),

    #attendance table on the DEO dashboard
    url(r'^emis/attendance/', generic, {
        'model':XFormSubmission,
        'queryset':AttendanceReport,
        'selectable':False,
        'paginated':False,
        'results_title':'Attendance',
        'columns':[
            ('', False, '', None),
            ('boys', False, '', None),
            ('girls', False, '', None),
            ('total pupils', False, '', None),
            ('male teachers', False, '', None),
            ('female teachers', False, '', None),
            ('total teachers', False, '', None),
        ],
        'partial_row':'education/partials/report_row.html',
        'partial_header':'education/partials/partial_header.html',
        'base_template':'generic/base.html',
        'needs_date':True,
        'dates':get_xform_dates,
    }, name='attendance-stats'),

    #GEM headteacher attendance report on DEO dashboard
    url(r'^emis/htattendance/', generic, {
        'model':XFormSubmission,
        'queryset':HtAttendanceReport,
        'selectable':False,
        'paginated':False,
        'results_title':'GEM Reported Head Teacher Attendance',
        'columns':[
            ('', False, '', None),
            ('head teacher attendance', False, '', None),
            ('head teacher deployment', False, '', None),
            ('percentage attendance', False, '', None),
        ],
        'partial_row':'education/partials/report_row.html',
        'partial_header':'education/partials/partial_header.html',
        'base_template':'generic/base.html',
        'needs_date':True,
        'dates':get_xform_dates,
    }, name='htattendance-stats'),

    #Enrollment report on DEO dashboard
    url(r'^emis/enrollment/', generic, {
        'model':XFormSubmission,
        'queryset':EnrollmentReport,
        'selectable':False,
        'paginated':False,
        'results_title':'Enrollment Report',
        'columns':[
            ('', False, '', None),
            ('boys', False, '', None),
            ('girls', False, '', None),
            ('total enrollment', False, '', None),
            ('male teachers', False, '', None),
            ('female teachers', False, '', None),
            ('total deployment', False, '', None),
        ],
        'partial_row':'education/partials/report_row.html',
        'partial_header':'education/partials/partial_header.html',
        'base_template':'generic/base.html',
        'needs_date':True,
        'dates':get_xform_dates,
    }, name='enrollment-stats'),

    #Abuse Cases report on DEO dashboard
    url(r'^emis/abuse/', generic, {
        'model':XFormSubmission,
        'queryset':AbuseReport,
        'selectable':False,
        'paginated':False,
        'results_title':'Child Abuse Cases Report',
        'columns':[
            ('', False, '', None),
            ('gem cases', False, '', None),
            ('head teacher cases', False, '', None),
        ],
        'partial_row':'education/partials/report_row.html',
        'partial_header':'education/partials/partial_header.html',
        'base_template':'generic/base.html',
        'needs_date':True,
        'dates':get_xform_dates,
    }, name='enrollment-stats'),

)
