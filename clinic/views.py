from functools import wraps
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum

from .models import (
    Department, ClinicRoom, Doctor, Patient,
    Schedule, Appointment, MedicalRecord, Payment
)
from .forms import PaymentForm, AppointmentForm  # 新增导入AppointmentForm

# ==================== 权限装饰器 ====================
def patient_required(view_func):
    """患者权限装饰器：仅允许已绑定患者信息的普通用户访问"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                # 检查用户是否绑定了Patient模型
                request.patient = request.user.patient
                return view_func(request, *args, **kwargs)
            except Patient.DoesNotExist:
                return redirect('patient_profile')
        return redirect('login')
    return wrapper

def reception_required(view_func):
    """前台权限装饰器：仅允许员工（非超级管理员）访问"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff and not request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper

def admin_required(view_func):
    """管理员权限装饰器：仅允许超级管理员访问"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper

# ==================== 通用视图 ====================
def login_view(request):
    """登录视图"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # 根据用户类型跳转对应仪表盘
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif user.is_staff:
                return redirect('reception_dashboard')
            else:
                return redirect('patient_dashboard')
        else:
            return render(request, 'registration/login.html', {'error': '用户名或密码错误'})
    return render(request, 'registration/login.html')

def logout_view(request):
    """登出视图"""
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    """根路径跳转：根据用户类型自动跳转对应仪表盘"""
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    elif request.user.is_staff:
        return redirect('reception_dashboard')
    else:
        return redirect('patient_dashboard')

# ==================== 患者视图 ====================
@login_required
@patient_required
def patient_dashboard(request):
    # 处理数据查询和切片
    upcoming_appointments = request.patient.appointment_set.filter(status=0)[:3]  # 在视图中处理
    return render(request, 'clinic/patient/dashboard.html', {
        'upcoming_appointments': upcoming_appointments  # 传递给模板
    })

@login_required
def patient_profile(request):
    """完善/修改患者信息"""
    try:
        patient = request.user.patient
    except Patient.DoesNotExist:
        patient = None

    if request.method == 'POST':
        # 保存患者信息
        name = request.POST.get('name')
        gender = request.POST.get('gender')
        id_card = request.POST.get('id_card')
        mobile = request.POST.get('mobile')
        birth_date = request.POST.get('birth_date')

        if patient:
            # 更新现有信息
            patient.name = name
            patient.gender = gender
            patient.id_card = id_card
            patient.mobile = mobile
            patient.birth_date = birth_date
            patient.save()
        else:
            # 创建新患者信息
            Patient.objects.create(
                user=request.user,
                name=name,
                gender=gender,
                id_card=id_card,
                mobile=mobile,
                birth_date=birth_date
            )
        return redirect('patient_dashboard')

    return render(request, 'clinic/patient/profile.html', {'patient': patient})

@login_required
@patient_required
def patient_appointment(request):
    """患者预约挂号（修复strptime空值问题，整合表单验证）"""
    form = AppointmentForm(request.POST or None)  # 初始化表单
    depts = Department.objects.all()  # 保留科室列表，兼容模板
    
    if request.method == 'POST':
        if form.is_valid():  # 先通过表单验证（自动处理空值、时间范围）
            dept = form.cleaned_data['dept']
            arrival_time = form.cleaned_data['arrival_time']
            
            # 检查预约冲突：同一患者同一时间段只能有一个未完成预约
            conflict = Appointment.objects.filter(
                patient=request.patient,
                status=0,
                arrival_time__date=arrival_time.date()  # 直接用datetime对象的date()，无需strptime
            ).exists()
            
            if conflict:
                return render(request, 'clinic/patient/appointment.html', {
                    'form': form,
                    'depts': depts,
                    'error': '您当天已有未完成的预约，请先处理后再新增'
                })
            
            # 创建预约（使用表单验证后的数据）
            Appointment.objects.create(
                patient=request.patient,
                dept=dept,
                appt_time=datetime.now(),
                arrival_time=arrival_time,  # 已验证的datetime对象
                status=0  # 0=未就诊
            )
            return redirect('patient_appointment_list')
        # 表单验证失败，返回错误信息
        else:
            return render(request, 'clinic/patient/appointment.html', {
                'form': form,
                'depts': depts,
                'error': '请检查填写的信息是否正确'
            })
    
    # GET请求，展示空表单
    return render(request, 'clinic/patient/appointment.html', {
        'form': form,
        'depts': depts
    })

@login_required
@patient_required
def patient_appointment_list(request):
    """患者预约列表"""
    appointments = Appointment.objects.filter(patient=request.patient).order_by('-appt_time')
    return render(request, 'clinic/patient/appointment_list.html', {'appointments': appointments})

# ==================== 前台视图 ====================
@login_required
@reception_required
def reception_dashboard(request):
    """前台仪表盘"""
    # 今日就诊人次
    today = datetime.now().date()
    today_visits = MedicalRecord.objects.filter(visit_time__date=today).count()
    # 今日缴费总额
    today_payments = Payment.objects.filter(pay_time__date=today).aggregate(total=Sum('total_amount'))['total'] or 0
    return render(request, 'clinic/reception/dashboard.html', {
        'today_visits': today_visits,
        'today_payments': today_payments
    })

@login_required
@reception_required
def reception_verify_appointment(request):
    """前台预约核验"""
    if request.method == 'POST':
        appt_id = request.POST.get('appt_id')
        try:
            appointment = Appointment.objects.get(id=appt_id, status=0)
            # 生成就诊记录
            MedicalRecord.objects.create(
                patient=appointment.patient,
                doctor=Doctor.objects.filter(dept=appointment.dept, work_status=True).first(),
                room=ClinicRoom.objects.filter(dept=appointment.dept).first(),
                visit_time=datetime.now(),
                visit_status=0  # 0=就诊中
            )
            # 更新预约状态为已完成
            appointment.status = 1
            appointment.save()
            return redirect('reception_visit_list')
        except Appointment.DoesNotExist:
            return render(request, 'clinic/reception/verify_appointment.html', {
                'error': '预约ID不存在或已完成/取消'
            })
    return render(request, 'clinic/reception/verify_appointment.html')

@login_required
@reception_required
def reception_payment(request):
    """前台缴费结算"""
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        total_amount = request.POST.get('total_amount')
        medical_insurance = request.POST.get('medical_insurance') or 0
        pay_method = request.POST.get('pay_method')
        
        try:
            record = MedicalRecord.objects.get(id=record_id, visit_status=0)
            # 创建缴费记录
            Payment.objects.create(
                record=record,
                total_amount=float(total_amount),
                medical_insurance=float(medical_insurance),
                self_pay=float(total_amount) - float(medical_insurance),
                pay_method=pay_method,
                pay_time=datetime.now()
            )
            # 更新就诊状态为已离院
            record.visit_status = 1
            record.save()
            return redirect('reception_payment_list')
        except MedicalRecord.DoesNotExist:
            return render(request, 'clinic/reception/payment.html', {
                'error': '就诊记录不存在或已缴费'
            })
    return render(request, 'clinic/reception/payment.html', {'form': PaymentForm()})

@login_required
@reception_required
def reception_visit_list(request):
    """前台就诊记录列表"""
    visit_records = MedicalRecord.objects.all().order_by('-visit_time')
    return render(request, 'clinic/reception/visit_list.html', {'visit_records': visit_records})

@login_required
@reception_required
def reception_payment_list(request):
    """前台缴费记录列表"""
    payments = Payment.objects.all().order_by('-pay_time')
    return render(request, 'clinic/reception/payment_list.html', {'payments': payments})

# ==================== 管理员视图 ====================
@login_required
@admin_required
def admin_dashboard(request):
    """管理员仪表盘"""
    # 总患者数
    total_patients = Patient.objects.count()
    # 总医生数
    total_doctors = Doctor.objects.count()
    # 总科室数
    total_depts = Department.objects.count()
    # 本月收入
    today = datetime.now()
    month_start = datetime(today.year, today.month, 1)
    month_payments = Payment.objects.filter(pay_time__gte=month_start).aggregate(total=Sum('total_amount'))['total'] or 0
    
    return render(request, 'clinic/admin/dashboard.html', {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_depts': total_depts,
        'month_payments': month_payments
    })

@login_required
@admin_required
def admin_schedule(request):
    """管理员排班管理"""
    schedules = Schedule.objects.all().order_by('-schedule_date')
    if request.method == 'POST':
        # 保存新排班
        doctor_id = request.POST.get('doctor')
        room_id = request.POST.get('room')
        schedule_date = request.POST.get('schedule_date')
        time_slot = request.POST.get('time_slot')
        status = request.POST.get('status')
        
        # 空值检查：避免strptime报错
        if not schedule_date:
            return render(request, 'clinic/admin/schedule.html', {
                'schedules': schedules,
                'error': '请选择排班日期'
            })
        
        Schedule.objects.create(
            doctor=get_object_or_404(Doctor, id=doctor_id),
            room=get_object_or_404(ClinicRoom, id=room_id),
            schedule_date=datetime.strptime(schedule_date, '%Y-%m-%d').date(),
            time_slot=time_slot,
            status=int(status)
        )
        return redirect('admin_schedule')
    
    return render(request, 'clinic/admin/schedule.html', {'schedules': schedules})

@login_required
@admin_required
def admin_statistics(request):
    """管理员数据统计"""
    # 按科室统计就诊人次
    dept_visits = MedicalRecord.objects.values('doctor__dept__dept_name').annotate(count=Count('id')).order_by('-count')
    total_visits = sum(item['count'] for item in dept_visits) if dept_visits else 0
    
    # 按医生统计收入
    doctor_payments = Payment.objects.values('record__doctor__name').annotate(
        total=Sum('total_amount'),
        medical_insurance__sum=Sum('medical_insurance'),
        self_pay__sum=Sum('self_pay')
    ).order_by('-total')
    
    return render(request, 'clinic/admin/statistics.html', {
        'dept_visits': dept_visits,
        'total_visits': total_visits,
        'doctor_payments': doctor_payments
    })