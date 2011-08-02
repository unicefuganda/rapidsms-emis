from django import forms
import datetime
from mptt.forms import TreeNodeChoiceField
from rapidsms.contrib.locations.models import Location
from generic.forms import ActionForm, FilterForm, ModuleForm
from mptt.forms import TreeNodeChoiceField
from rapidsms.contrib.locations.models import Location
from .models import School

date_range_choices = (('w', 'Previous Calendar Week'), ('m', 'Previous Calendar Month'), ('q', 'Previous calendar quarter'),)

class DateRangeForm(forms.Form): # pragma: no cover
    start_ts = forms.IntegerField(required=True, widget=forms.HiddenInput())
    end_ts = forms.IntegerField(required=True, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = self.cleaned_data

        start_ts = cleaned_data.get('start_ts')
        cleaned_data['start_ts'] = datetime.datetime.fromtimestamp(float(start_ts) / 1000.0)

        end_ts = cleaned_data.get('end_ts')
        cleaned_data['end_ts'] = datetime.datetime.fromtimestamp(float(end_ts) / 1000.0)
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
            return queryset.filter(school=None)
        else:
            return queryset.filter(school=school_pk)
