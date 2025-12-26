from django.contrib import admin
from .models import (
    Department, ClinicRoom, Doctor, Patient,
    Schedule, Appointment, MedicalRecord, Payment
)

# 注册模型到后台
admin.site.register(Department)
admin.site.register(ClinicRoom)
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(Schedule)
admin.site.register(Appointment)
admin.site.register(MedicalRecord)
admin.site.register(Payment)

# 优化后台显示（可选，让后台更友好）
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'dept', 'title', 'mobile', 'work_status')
    search_fields = ('name', 'dept__dept_name')

class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'id_card', 'mobile', 'birth_date')
    search_fields = ('name', 'id_card')

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'dept', 'appt_time', 'arrival_time', 'status')
    list_filter = ('status', 'dept')

# 重新注册优化后的模型
admin.site.unregister(Doctor)
admin.site.register(Doctor, DoctorAdmin)
admin.site.unregister(Patient)
admin.site.register(Patient, PatientAdmin)
admin.site.unregister(Appointment)
admin.site.register(Appointment, AppointmentAdmin)