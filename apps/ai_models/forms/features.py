from django import forms

from ai_models.models import SsqFeatureSet
from utils.bootstrap5 import Bootstrap5FormMixin


class SsqFeatureSetForm(Bootstrap5FormMixin, forms.ModelForm):
    """特征FORM"""
    class Meta:
        model = SsqFeatureSet
        fields = ['name', 'description', 'period_start', 'period_end']