from django import forms

from .models import SourceType, VerificationState, WalkableNode, WalkableSegment


class WalkableNodeForm(forms.ModelForm):
    class Meta:
        model = WalkableNode
        fields = ("label", "latitude", "longitude", "is_active")
        widgets = {"latitude": forms.HiddenInput, "longitude": forms.HiddenInput}

    def __init__(self, *args, locked=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.locked = locked
        for field in self.fields.values(): field.widget.attrs.setdefault("class", "editor-input")

    def clean(self):
        cleaned = super().clean()
        if self.locked and self.instance.pk and any(x in self.changed_data for x in ("latitude", "longitude")):
            raise forms.ValidationError("Connected nodes cannot be moved. Split or replace affected segments explicitly.")
        return cleaned

    def save(self, commit=True):
        item = super().save(commit=False)
        if item._state.adding:
            item.source_type = SourceType.MANUAL
            item.verification_state = VerificationState.UNVERIFIED
        elif any(name in self.changed_data for name in ("latitude", "longitude")):
            item.verification_state = VerificationState.UNVERIFIED
        if commit: item.save()
        return item


class WalkableSegmentForm(forms.ModelForm):
    class Meta:
        model = WalkableSegment
        fields = ("label", "start_node", "end_node", "geometry", "is_bidirectional", "is_active")
        widgets = {"geometry": forms.HiddenInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values(): field.widget.attrs.setdefault("class", "editor-input")

    def clean_geometry(self):
        geometry = self.cleaned_data.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") != "LineString":
            raise forms.ValidationError("Draw a valid path on the map.")
        return geometry

    def save(self, commit=True):
        item = super().save(commit=False)
        if item._state.adding:
            item.source_type = SourceType.MANUAL
            item.verification_state = VerificationState.UNVERIFIED
        elif any(name in self.changed_data for name in ("start_node", "end_node", "geometry")):
            item.verification_state = VerificationState.UNVERIFIED
        if commit: item.save()
        return item


class SplitSegmentForm(forms.Form):
    latitude = forms.DecimalField(max_digits=8, decimal_places=6, widget=forms.HiddenInput)
    longitude = forms.DecimalField(max_digits=9, decimal_places=6, widget=forms.HiddenInput)
