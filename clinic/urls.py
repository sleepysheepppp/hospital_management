from django.urls import path
from . import views

urlpatterns = [
    # 通用路由
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # 患者路由
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/profile/', views.patient_profile, name='patient_profile'),
    path('patient/appointment/', views.patient_appointment, name='patient_appointment'),
    path('patient/appointment/list/', views.patient_appointment_list, name='patient_appointment_list'),
    path('patient/appointment/<int:appt_id>/', views.appointment_detail, name='appointment_detail'),
    path('patient/appointment/<int:appt_id>/cancel/', views.appointment_cancel, name='appointment_cancel'),

    # 前台路由（核心修复：统一路由名，补充缺失路由）
    path('reception/dashboard/', views.reception_dashboard, name='reception_dashboard'),
    # 修复1：路由名改为 verify_appointment（匹配模板中的引用）
    path('reception/verify/', views.reception_verify_appointment, name='verify_appointment'),
    # 修复2：路由名改为 payment（匹配模板中的引用）
    path('reception/payment/', views.reception_payment, name='payment'),
    path('reception/visit/list/', views.reception_visit_list, name='reception_visit_list'),
    path('reception/payment/list/', views.reception_payment_list, name='reception_payment_list'),

    # 管理员路由（补充缺失的路由名）
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # 修复3：添加 schedule_management 路由名（匹配模板）
    path('admin/schedule/', views.admin_schedule, name='schedule_management'),
    # 修复4：添加 statistics 路由名（匹配模板）
    path('admin/statistics/', views.admin_statistics, name='statistics'),

    # 新增医生首页路由
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    
]