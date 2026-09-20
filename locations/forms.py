from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Category, Location, LocationAlias


LEGACY_CATEGORY_PRIORITY = (
    ("food-snacks", Location.Category.FOOD),
    ("medical", Location.Category.HEALTH),
    ("library-study", Location.Category.LIBRARY),
    ("accommodation", Location.Category.HOSTEL),
    ("administration", Location.Category.OFFICE),
    ("academic", Location.Category.BUILDING),
)


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ("name", "description", "place_type", "categories", "publication_status")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "categories": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categories"].queryset = Category.objects.filter(is_active=True)
        self.fields["publication_status"].choices = Location.PublicationStatus.choices
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "editor-input")

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
