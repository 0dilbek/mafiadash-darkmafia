import re

from django import forms

from .cinema_models import CinemaMovie, CinemaPlan


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


class CinemaMovieForm(CinemaModelForm):
    message_text = forms.CharField(label="Kino xabari", max_length=4096, required=False, widget=forms.Textarea)

    class Meta:
        model = CinemaMovie
        fields = ("code", "file_id", "message_text")
        labels = {"code": "Kino kodi", "file_id": "Telegram video file_id"}

    def clean_code(self):
        code = self.cleaned_data["code"].strip().casefold()
        if not re.fullmatch(r"[a-z0-9_-]{1,64}", code):
            raise forms.ValidationError("Kod 1–64 ta lotin harfi, raqam, '_' yoki '-' belgisidan iborat bo'lsin.")
        return code
