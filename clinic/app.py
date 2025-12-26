from django.apps import AppConfig

class ClinicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic'
    verbose_name = '门诊管理'  # 后台显示的应用名称