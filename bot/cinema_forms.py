from django import forms

from .cinema_models import CinemaPlan


class CinemaModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"


class CinemaPlanForm(CinemaModelForm):
    price_diamonds = forms.IntegerField(label="Obuna narxi (💎)", min_value=1, max_value=10**12)
    duration_days = forms.IntegerField(label="Obuna muddati (kun)", min_value=1, max_value=3650)

    class Meta:
        model = CinemaPlan
        fields = ("price_diamonds", "duration_days", "is_enabled")
        labels = {"is_enabled": "Pulli obuna savdosini yoqish"}
