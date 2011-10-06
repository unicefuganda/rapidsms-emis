from django import forms
import datetime
from mptt.forms import TreeNodeChoiceField
from rapidsms.contrib.locations.models import Location
from generic.forms import ActionForm, FilterForm, ModuleForm
from mptt.forms import TreeNodeChoiceField
from rapidsms.contrib.locations.models import Location
from .models import School, EmisReporter
from rapidsms_xforms.models import XFormSubmissionValue
from django.contrib.auth.models import Group

date_range_choices = (('w', 'Previous Calendar Week'), ('m', 'Previous Calendar Month'), ('q', 'Previous calendar quarter'),)

class DateRangeForm(forms.Form): # pragma: no cover
    start = forms.IntegerField(required=True, widget=forms.HiddenInput())
    end = forms.IntegerField(required=True, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = self.cleaned_data

        start_ts = cleaned_data.get('start')
        cleaned_data['start'] = datetime.datetime.fromtimestamp(float(start_ts))

        end_ts = cleaned_data.get('end')
        cleaned_data['end'] = datetime.datetime.fromtimestamp(float(end_ts))
        return cleaned_data

AREAS = Location.tree.all().select_related('type')

class SchoolFilterForm(FilterForm):
    """ filter form for emis schools """
    school = forms.ChoiceField(choices=(('', '-----'), (-1, 'Has No School'),) + tuple(School.objects.values_list('pk', 'name').order_by('name')))


    def filter(self, request, queryset):
        school_pk = self.cleaned_data['school']
        if school_pk == '':
            return queryset
        elif int(school_pk) == -1:
            return queryset.filter(schools__name=None)
        else:
            return queryset.filter(schools=school_pk)

class NewConnectionForm(forms.Form):
    identity = forms.CharField(max_length=15, required=True, label="Primary contact information")

class EditReporterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
           super(EditReporterForm, self).__init__(*args, **kwargs)
           self.fields['reporting_location'] = TreeNodeChoiceField(queryset=self.fields['reporting_location'].queryset, level_indicator=u'.')

    class Meta:
        model = EmisReporter
        fields = ('name', 'reporting_location', 'groups', 'schools')

class DistrictFilterForm(forms.Form):
    """ filter form for districts """
    locs = Location.objects.filter(name__in=XFormSubmissionValue.objects.values_list('submission__connection__contact__reporting_location__name', flat=True))
    locs_list = []
    for loc in locs:
        if not Location.tree.root_nodes()[0].pk == loc.pk and loc.type.name == 'district':
            locs_list.append((loc.pk, loc.name))
    district = forms.ChoiceField(choices=(('', '-----'),) + tuple(locs_list))

class LimitedDistictFilterForm(FilterForm):

    """ filter Emis Reporters on their districts """

    locs = Location.objects.filter(name__in=XFormSubmissionValue.objects.values_list('submission__connection__contact__reporting_location__name', flat=True)).order_by('name')
    locs_list = []
    for loc in locs:
        if not Location.tree.root_nodes()[0].pk == loc.pk and loc.type.name == 'district':
            locs_list.append((loc.pk, loc.name))
    district = forms.ChoiceField(choices=(('', '-----'),) + tuple(locs_list))

    def filter(self, request, queryset):
        district_pk = self.cleaned_data['district']
        if district_pk == '':
            return queryset
        elif int(district_pk) == -1:
            return queryset.filter(reporting_location=None)
        else:

            try:
                district = Location.objects.get(pk=district_pk)
            except Location.DoesNotExist:
                district = None
            if district:
                return queryset.filter(reporting_location__in=district.get_descendants(include_self=True))
            else:
                return queryset

class RolesFilterForm(FilterForm):
    def __init__(self, data=None, **kwargs):
        self.request = kwargs.pop('request')
        if data:
            forms.Form.__init__(self, data, **kwargs)
        else:
            forms.Form.__init__(self, **kwargs)
        choices = ((-1, 'No Group'),) + tuple([(int(g.pk), g.name) for g in Group.objects.all().order_by('name')])
        self.fields['groups'] = forms.ChoiceField(choices=choices, required=True)


    def filter(self, request, queryset):
        groups_pk = self.cleaned_data['groups']
        if groups_pk == '-1':
            return queryset.filter(groups=None)
        else:
            return queryset.filter(groups=groups_pk)

