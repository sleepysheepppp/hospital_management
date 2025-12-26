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

    # 前台路由
    path('reception/dashboard/', views.reception_dashboard, name='reception_dashboard'),
    path('reception/verify/', views.reception_verify_appointment, name='reception_verify_appointment'),
    path('reception/payment/', views.reception_payment, name='reception_payment'),
    path('reception/visit/list/', views.reception_visit_list, name='reception_visit_list'),
    path('reception/payment/list/', views.reception_payment_list, name='reception_payment_list'),

    # 管理员路由
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/schedule/', views.admin_schedule, name='admin_schedule'),
    path('admin/statistics/', views.admin_statistics, name='admin_statistics'),
]