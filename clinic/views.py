from functools import wraps
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.contrib import messages  # 新增：用于提示信息
from django.utils import timezone
from .models import Patient 

from .models import (
    Department, ClinicRoom, Doctor, Patient,
    Schedule, Appointment, MedicalRecord, Payment
)
from .forms import PaymentForm, AppointmentForm

# ==================== 权限装饰器 ====================
def patient_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                request.patient = request.user.patient
                return view_func(request, *args, **kwargs)
            except Patient.DoesNotExist:
                return redirect('patient_profile')
        return redirect('login')
    return wrapper

# （其他装饰器保持不变）
def reception_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff and not request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper

# ==================== 通用视图 ====================


def login_view(request):
    # 已登录用户直接跳对应首页，避免重复登录
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # 增加空值校验，避免空账号密码提交
        if not username or not password:
            return render(request, 'registration/login.html', {'error': '请输入用户名和密码'})
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # 按角色精准跳转，补充医生角色判断（通过user.groups或自定义字段）
            if user.is_superuser:
                # 超级管理员 → 管理员首页
                return redirect('admin_dashboard')
            elif user.is_staff:
                # 区分医生和前台（推荐用用户组，若无则先跳前台/医生通用首页）
                # 方式1：通过用户组判断（需先在后台给医生/前台建对应组）
                if user.groups.filter(name='医生').exists():
                    return redirect('doctor_dashboard')  # 医生首页
                elif user.groups.filter(name='前台').exists():
                    return redirect('reception_dashboard')  # 前台首页
                # 方式2：无用户组时，默认跳前台首页（兼容原有逻辑）
                else:
                    return redirect('reception_dashboard')
            else:
                # 普通患者：先检查是否完善信息
                try:
                    # 已完善患者信息 → 患者首页
                    request.user.patient
                    return redirect('patient_dashboard')
                except Patient.DoesNotExist:
                    # 未完善信息 → 跳信息完善页
                    messages.info(request, '请先完善您的患者信息')
                    return redirect('patient_profile')
        else:
            return render(request, 'registration/login.html', {'error': '用户名或密码错误'})
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, '已成功退出登录')
    return redirect('login')

@login_required
def dashboard(request):
    """通用首页路由，按角色分发到对应专属首页"""
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    elif request.user.is_staff:
        # 同样区分医生/前台
        if request.user.groups.filter(name='医生').exists():
            return redirect('doctor_dashboard')
        else:
            return redirect('reception_dashboard')
    else:
        # 患者：强制检查信息完善状态
        try:
            request.user.patient
            return redirect('patient_dashboard')
        except Patient.DoesNotExist:
            messages.info(request, '请先完善您的患者信息')
            return redirect('patient_profile')

# ==================== 患者视图 ====================
@login_required
@patient_required
def patient_dashboard(request):
    # 修复：确保待就诊列表包含所有未就诊预约（不限制数量，原逻辑保留切片但确保新预约能显示）
    upcoming_appointments = request.patient.appointment_set.filter(status=0).order_by('arrival_time')[:3]
    return render(request, 'clinic/patient/dashboard.html', {
        'upcoming_appointments': upcoming_appointments
    })

@login_required
def patient_profile(request):
    # （保持不变）
    try:
        patient = request.user.patient
    except Patient.DoesNotExist:
        patient = None

    if request.method == 'POST':
        name = request.POST.get('name')
        gender = request.POST.get('gender')
        id_card = request.POST.get('id_card')
        mobile = request.POST.get('mobile')
        birth_date = request.POST.get('birth_date')

        if patient:
            patient.name = name
            patient.gender = gender
            patient.id_card = id_card
            patient.mobile = mobile
            patient.birth_date = birth_date
            patient.save()
        else:
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
    """修复：确保提交后正确跳转并提示成功信息"""
    form = AppointmentForm(request.POST or None)
    depts = Department.objects.all()
    
    if request.method == 'POST':
        if form.is_valid():
            dept = form.cleaned_data['dept']
            arrival_time = form.cleaned_data['arrival_time']
            
            conflict = Appointment.objects.filter(
                patient=request.patient,
                status=0,
                arrival_time__date=arrival_time.date()
            ).exists()
            
            if conflict:
                return render(request, 'clinic/patient/appointment.html', {
                    'form': form,
                    'depts': depts,
                    'error': '您当天已有未完成的预约，请先处理后再新增'
                })
            
            # 创建预约
            Appointment.objects.create(
                patient=request.patient,
                dept=dept,
                appt_time=timezone.now(),
                arrival_time=arrival_time,
                status=0  # 0=未就诊
            )
            # 新增：添加成功提示
            messages.success(request, "预约提交成功！")
            # 修复：提交后返回患者首页（原逻辑跳转到列表，根据需求调整）
            return redirect('patient_dashboard')
        else:
            return render(request, 'clinic/patient/appointment.html', {
                'form': form,
                'depts': depts,
                'error': '请检查填写的信息是否正确'
            })
    
    return render(request, 'clinic/patient/appointment.html', {
        'form': form,
        'depts': depts
    })

@login_required
@patient_required
def patient_appointment_list(request):
    """患者预约列表（保持不变，为模板提供数据）"""
    appointments = Appointment.objects.filter(patient=request.patient).order_by('-appt_time')
    return render(request, 'clinic/patient/appointment_list.html', {'appointments': appointments})

@login_required
@patient_required
def appointment_detail(request, appt_id):
    """查看预约详情（修复：用appt_id查询，匹配模型主键）"""
    # 修复：查询条件用 appt_id=appt_id（不是 id=appt_id）
    appointment = get_object_or_404(
        Appointment, 
        appt_id=appt_id,  # 关键：模型主键是appt_id，不是id
        patient=request.patient
    )
    return render(request, 'clinic/patient/appointment_detail.html', {
        'appointment': appointment
    })

@login_required
@patient_required
def appointment_cancel(request, appt_id):
    """取消预约（修复：用appt_id查询）"""
    appointment = get_object_or_404(
        Appointment, 
        appt_id=appt_id,  # 关键：模型主键是appt_id
        patient=request.patient,
        status=0  # 仅允许取消未就诊状态
    )
    appointment.status = 2  # 2=已取消
    appointment.save()
    messages.success(request, "预约已成功取消")
    return redirect('patient_appointment_list')

# ==================== 前台视图 ====================
# （所有前台视图保持不变）
@login_required
@reception_required
def reception_dashboard(request):
    today = datetime.now().date()
    today_visits = MedicalRecord.objects.filter(visit_time__date=today).count()
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
    visit_records = MedicalRecord.objects.all().order_by('-visit_time')
    return render(request, 'clinic/reception/visit_list.html', {'visit_records': visit_records})

@login_required
@reception_required
def reception_payment_list(request):
    payments = Payment.objects.all().order_by('-pay_time')
    return render(request, 'clinic/reception/payment_list.html', {'payments': payments})

# ==================== 管理员视图 ====================
# （所有管理员视图保持不变）
@login_required
@admin_required
def admin_dashboard(request):
    total_patients = Patient.objects.count()
    total_doctors = Doctor.objects.count()
    total_depts = Department.objects.count()
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
    schedules = Schedule.objects.all().order_by('-schedule_date')
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        room_id = request.POST.get('room')
        schedule_date = request.POST.get('schedule_date')
        time_slot = request.POST.get('time_slot')
        status = request.POST.get('status')
        
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
    dept_visits = MedicalRecord.objects.values('doctor__dept__dept_name').annotate(count=Count('id')).order_by('-count')
    total_visits = sum(item['count'] for item in dept_visits) if dept_visits else 0
    
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

# ==================== 医生视图 ====================
@login_required
def doctor_dashboard(request):
    """医生专属首页（仅staff且属于医生组的用户可访问）"""
    # 权限校验：非医生组的staff用户强制跳前台首页
    if not request.user.groups.filter(name='医生').exists():
        return redirect('reception_dashboard')
    
    # 医生首页逻辑（示例：显示今日接诊预约）
    today = timezone.now().date()
    # 可根据实际业务补充逻辑
    context = {
        'page_title': '医生首页',
        'today': today
    }
    return render(request, 'clinic/doctor/dashboard.html', context)

@login_required
def patient_profile(request):
    """患者信息完善页（仅普通患者可访问）"""
    # 权限校验：staff/管理员禁止访问
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard')
    
    patient = None
    try:
        patient = request.user.patient
    except Patient.DoesNotExist:
        pass
    
    if request.method == 'POST':
        # 处理患者信息提交逻辑（示例）
        name = request.POST.get('name')
        gender = request.POST.get('gender')
        mobile = request.POST.get('mobile')
        # 保存患者信息
        Patient.objects.update_or_create(
            user=request.user,
            defaults={'name': name, 'gender': gender, 'mobile': mobile}
        )
        messages.success(request, '信息完善成功！')
        return redirect('patient_dashboard')
    
    return render(request, 'clinic/patient/profile.html', {'patient': patient})