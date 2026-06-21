"""Django admin registrations for the Schools & Formations referential — Story 4.1 / 4.8."""

from __future__ import annotations

from typing import ClassVar

from django.contrib import admin

from apps.schools.models import FavoriteSchool, Formation, School


class FormationInline(admin.TabularInline):
    model = Formation
    extra = 0
    fields = ("name", "duration_years", "parcoursup_open", "affelnet_open")
    readonly_fields = ("id",)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display: ClassVar = (
        "name",
        "type",
        "city",
        "region",
        "public_private",
        "selectivity_index",
    )
    list_filter: ClassVar = ("type", "region", "public_private", "apprenticeship", "internship")
    search_fields: ClassVar = ("name", "city", "slug")
    prepopulated_fields: ClassVar = {"slug": ("name",)}
    inlines: ClassVar = [FormationInline]
    readonly_fields: ClassVar = ("id", "created_at", "updated_at")


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display: ClassVar = (
        "name",
        "school",
        "duration_years",
        "parcoursup_open",
        "affelnet_open",
    )
    list_filter: ClassVar = ("parcoursup_open", "affelnet_open", "duration_years")
    search_fields: ClassVar = ("name", "school__name")
    readonly_fields: ClassVar = ("id", "created_at")
    autocomplete_fields: ClassVar = ("school",)


@admin.register(FavoriteSchool)
class FavoriteSchoolAdmin(admin.ModelAdmin):
    list_display: ClassVar = ("user", "school", "created_at")
    list_filter: ClassVar = ("created_at",)
    search_fields: ClassVar = ("user__email", "school__name", "school__slug")
    readonly_fields: ClassVar = ("id", "created_at")
    autocomplete_fields: ClassVar = ("school",)
