from django.conf.urls.defaults import *
from .views import index, report, get_dates
from django.conf.urls.defaults import *
from generic.views import generic, generic_row, generic_dashboard, generic_map
from generic.sorters import SimpleSorter, TupleSorter
from contact.forms import FreeSearchForm, DistictFilterForm, MassTextForm
from .forms import SchoolFilterForm
from .sorters import LatestSubmissionSorter
from rapidsms_xforms.models import XForm, XFormSubmission
from rapidsms_httprouter.models import Message
from .models import EmisReporter
from contact.forms import FreeSearchTextForm, DistictFilterMessageForm, HandledByForm, ReplyTextForm
from .reports import MainEmisReport

urlpatterns = patterns('',
   url(r'^emis/stats/$', index, name='stats'),
   url(r'^emis/stats/(?P<location_id>\d+)/$', index),
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
    url(r'^emis/test/$', generic, {
        'model':XFormSubmission,
        'queryset':MainEmisReport,
        'selectable':False,
        'paginated':False,
        'results_title':None,
        'columns':[('', False, '', None),
            ('boys enrolled', False, '', None),
            ('girls enrolled', False, '', None),
            ('boys enrolled', False, '', None),
            ('girls enrolled', False, '', None),
            ('boys enrolled', False, '', None),
            ('girls enrolled', False, '', None),
            ('boys enrolled', False, '', None),
            ('girls enrolled', False, '', None),
            ('males deployed', False, '', None),
            ('females deployed', False, '', None),
            ('reported incidents', False, '', None),
            ('total for p4', False, '', None),
        ],
        'partial_row':'education/partials/attendance_row.html',
        'partial_header':'education/partials/partial_header.html',
        'base_template':'generic/timeslider_base.html',
        'needs_date':True,
        'dates':get_dates,
    })

)
