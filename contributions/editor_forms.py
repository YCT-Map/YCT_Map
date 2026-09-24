from django import forms

from .models import ContributionResolution


class ContributionResolutionForm(forms.ModelForm):
    class Meta:
        model = ContributionResolution
        fields = ("action", "location", "entrance", "walkable_node", "walkable_segment", "note")
        widgets = {"note": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "editor-input")
