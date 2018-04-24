from django.core.urlresolvers import reverse
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from braces.views import LoginRequiredMixin, PermissionRequiredMixin
from appconf.models import Settings
from organizations.models import Organization
from .api import ResultSerializer
from .forms import CreateLogFrameForm
from .mixins import AptivateDataBaseMixin
from .models import (
    Assumption, Indicator, LogFrame, Milestone, Result, ResultLevelName,
    RiskRating, SubIndicator, Target
)


class ResultEditor(LoginRequiredMixin, AptivateDataBaseMixin, DetailView):
    model = Result
    template_name = 'logframe/result.html'

    def get_logframe(self):
        return self.object.log_frame

    def get_data(self, logframe, data):
        """
        Get a dict containing all the data for one logframe
        """
        result = self.object
        data.update({
            'result': ResultSerializer(result).data,
            'riskratings': self._json_object_list(
                RiskRating.objects.all(),
                model_class=RiskRating),
            'assumptions': self._json_object_list(
                logframe.all_assumptions(),
                model_class=Assumption),
            'indicators': self.get_related_model_data(
                {'result': result},
                Indicator),
            'subindicators': self.get_related_model_data(
                {'indicator__result': result},
                SubIndicator),
            'targets': self.get_related_model_data(
                {'subindicator__indicator__result': result},
                Target),
            'milestones': self.get_related_model_data(
                {'log_frame': result.log_frame},
                Milestone),
        })
        return data


class ResultMonitor(LoginRequiredMixin, AptivateDataBaseMixin, DetailView):
    model = Result
    template_name = 'logframe/result.html'

    def get_logframe(self):
        return self.object.log_frame

    def get_data(self, logframe, data):
        """
        Get a dict containing all the data for one logframe
        """
        data.update({
            'result': ResultSerializer(self.object).data,
        })
        return data


class ManageLogFrame(PermissionRequiredMixin):
    model = LogFrame
    permission_required = 'logframe.edit_logframe'

    def get_success_url(self):
        return reverse('logframe-dashboard', kwargs={'slug': self.object.slug, 'org_slug': self.object.organization.slug})


class CreateLogframe(ManageLogFrame, CreateView):
    form_class = CreateLogFrameForm
    template_name = 'logframe/create_logframe.html'

    def add_result_levels(self):
        ResultLevelName.objects.bulk_create([
            ResultLevelName(level_number=1, level_name='Goal', logframe=self.object),
            ResultLevelName(level_number=2, level_name='Outcome', logframe=self.object),
            ResultLevelName(level_number=3, level_name='Output', logframe=self.object),
            ResultLevelName(level_number=4, level_name='Activity', logframe=self.object)
        ])

    def form_valid(self, form):
        # The logframe needs to exist before we create the settings, so finish
        # the regular form_valid code.
        form.instance.organization = Organization.objects.get(slug=self.kwargs['org_slug'])
        response = CreateView.form_valid(self, form)
        Settings.objects.create(logframe=form.instance)
        self.add_result_levels()
        return response


class EditLogframe(ManageLogFrame, UpdateView):
    fields = ['name', 'slug']
    template_name = 'logframe/edit_logframe.html'


class DeleteLogframe(ManageLogFrame, DeleteView):
    def get_success_url(self):
        return reverse('dashboard')
