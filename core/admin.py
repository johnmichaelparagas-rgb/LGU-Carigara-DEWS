from django.contrib import admin
from django.utils.html import format_html

from .models import AuditLog, HazardImage, Incident, Reading, Sensor, Warning


def _img_tag(obj, height):
    src = ''
    if obj.thumbnail:
        src = obj.thumbnail.url
    elif obj.image:
        src = obj.image.url
    if not src:
        return '—'
    return format_html('<img src="{}" style="height:{}px;border-radius:6px;" />', src, height)

admin.site.site_header = 'Carigara DEWS Administration'
admin.site.site_title = 'Carigara DEWS'
admin.site.index_title = 'MDRRMO Carigara Control Panel'


class ReadingInline(admin.TabularInline):
    model = Reading
    extra = 0
    readonly_fields = ('recorded_at',)


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hazard_type', 'municipality', 'status', 'online', 'updated_at')
    list_filter = ('hazard_type', 'status', 'municipality', 'online')
    search_fields = ('name', 'device_id', 'barangay')
    inlines = [ReadingInline]


class HazardImageInline(admin.TabularInline):
    model = HazardImage
    extra = 0
    fields = ('preview', 'image', 'caption', 'uploaded_at')
    readonly_fields = ('preview', 'uploaded_at')

    @admin.display(description='Preview')
    def preview(self, obj):
        return _img_tag(obj, 80)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('type', 'municipality', 'severity', 'status', 'reported_at')
    list_filter = ('type', 'severity', 'status', 'municipality')
    search_fields = ('summary', 'barangay', 'reporter_name')
    inlines = [HazardImageInline]


@admin.register(HazardImage)
class HazardImageAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'incident', 'caption', 'uploaded_at')
    list_display_links = ('thumb', 'incident')
    readonly_fields = ('thumb', 'uploaded_at')

    @admin.display(description='Image')
    def thumb(self, obj):
        return _img_tag(obj, 55)


@admin.register(Warning)
class WarningAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'hazard_type', 'active', 'issued_at')
    list_filter = ('level', 'hazard_type', 'active')
    search_fields = ('title', 'message')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('at', 'actor_name', 'action')
    list_filter = ('action',)
    readonly_fields = ('at', 'actor', 'actor_name', 'action', 'details')

    def has_add_permission(self, request):
        return False
