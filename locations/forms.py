from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Category, Entrance, Floor, InternalPlace, InternalPlaceAlias, Location, LocationAlias


LEGACY_CATEGORY_PRIORITY = (
    ("food-snacks", Location.Category.FOOD),
    ("medical", Location.Category.HEALTH),
    ("library-study", Location.Category.LIBRARY),
    ("accommodation", Location.Category.HOSTEL),
    ("administration", Location.Category.OFFICE),
    ("academic", Location.Category.BUILDING),
)


class LocationForm(forms.ModelForm):
    capture_primary_entrance = forms.BooleanField(required=False, label="Use this point for the primary entrance")
    confirm_primary_overwrite = forms.BooleanField(required=False, label="Replace the existing primary entrance point")

    class Meta:
        model = Location
        fields = ("name", "description", "place_type", "categories", "publication_status",
                  "representative_latitude", "representative_longitude")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "categories": forms.CheckboxSelectMultiple,
            "representative_latitude": forms.HiddenInput,
            "representative_longitude": forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categories"].queryset = Category.objects.filter(is_active=True)
        self.fields["publication_status"].choices = Location.PublicationStatus.choices
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "editor-input")

    def clean(self):
        cleaned = super().clean()
        latitude, longitude = cleaned.get("representative_latitude"), cleaned.get("representative_longitude")
        if (latitude is None) != (longitude is None):
            raise forms.ValidationError("Choose a complete representative point on the map.")
        if cleaned.get("capture_primary_entrance") and latitude is None:
            raise forms.ValidationError("Choose a map point before creating or updating a primary entrance.")
        existing_primary = self.instance.pk and self.instance.entrances.filter(is_primary=True, is_active=True).exists()
        if existing_primary and cleaned.get("capture_primary_entrance") and not cleaned.get("confirm_primary_overwrite"):
            raise forms.ValidationError("Confirm before replacing the existing primary entrance point.")
        return cleaned

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Enter a place name.")
        return name

    def clean_description(self):
        return self.cleaned_data["description"].strip()

    def clean_categories(self):
        categories = self.cleaned_data["categories"]
        if categories.filter(is_active=False).exists():
            raise forms.ValidationError("Choose only active categories.")
        return categories

    def save(self, commit=True):
        location = super().save(commit=False)
        location.is_active = location.publication_status == Location.PublicationStatus.PUBLISHED
        if commit:
            location.save()
            self.save_m2m()
            self._sync_legacy_category(location)
        return location

    def _sync_legacy_category(self, location):
        selected_slugs = set(location.categories.values_list("slug", flat=True))
        legacy_value = Location.Category.BUILDING
        for slug, candidate in LEGACY_CATEGORY_PRIORITY:
            if slug in selected_slugs:
                legacy_value = candidate
                break
        if location.category != legacy_value:
            Location.objects.filter(pk=location.pk).update(category=legacy_value)
            location.category = legacy_value


class AliasFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        names = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            name = form.cleaned_data.get("name", "").strip()
            if not name:
                continue
            normalized = name.casefold()
            if normalized in names:
                form.add_error("name", "This alias is already used for this place.")
            names.add(normalized)


class LocationAliasForm(forms.ModelForm):
    class Meta:
        model = LocationAlias
        fields = ("name", "alias_kind")

    def has_changed(self):
        name = str(self.data.get(self.add_prefix("name"), "")).strip()
        if not name and not self.instance.pk:
            return False
        return super().has_changed()


LocationAliasFormSet = inlineformset_factory(
    Location,
    LocationAlias,
    form=LocationAliasForm,
    formset=AliasFormSet,
    fields=("name", "alias_kind"),
    extra=2,
    can_delete=True,
)


class EntranceForm(forms.ModelForm):
    class Meta:
        model = Entrance
        fields = ("name", "entrance_type", "latitude", "longitude", "is_primary", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "editor-input")
        self.fields["latitude"].widget = forms.HiddenInput()
        self.fields["longitude"].widget = forms.HiddenInput()


class FloorForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ("level", "label", "display_order", "is_active")

    def clean_level(self):
        level = self.cleaned_data["level"]
        location_id = self.instance.location_id
        if location_id:
            duplicate = Floor.objects.filter(location_id=location_id, level=level)
            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise forms.ValidationError("A floor with this level already exists for this place.")
        return level


class InternalPlaceForm(forms.ModelForm):
    class Meta:
        model = InternalPlace
        fields = ("name", "internal_type", "floor", "room_code", "wing_section", "direction_note",
                  "routing_entrance", "publication_status")
        widgets = {"direction_note": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, location=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = location or getattr(self.instance, "location", None)
        if self.location and self.location.pk:
            self.fields["floor"].queryset = self.location.floors.order_by("display_order", "level")
            self.fields["routing_entrance"].queryset = self.location.entrances.filter(is_active=True)
        else:
            self.fields["floor"].queryset = Floor.objects.none()
            self.fields["routing_entrance"].queryset = Entrance.objects.none()
        self.fields["routing_entrance"].empty_label = "Use parent primary entrance"
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "editor-input")


InternalPlaceAliasFormSet = inlineformset_factory(
    InternalPlace, InternalPlaceAlias, formset=AliasFormSet,
    fields=("name", "alias_kind"), extra=2, can_delete=True,
)
