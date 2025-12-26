from django import forms
from .models import Patient, Appointment, Payment, Schedule
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.utils import timezone  # 新增：引入时区工具

# 患者预约表单
class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['dept', 'arrival_time']
        widgets = {
            'dept': forms.Select(attrs={'class': 'form-select'}),
            'arrival_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'required': True
                },
                # 修复：指定格式为前端兼容的ISO格式
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def clean_arrival_time(self):
        arrival_time = self.cleaned_data.get('arrival_time')
        if not arrival_time:
            raise ValidationError("请选择预计到达时间")
        
        # 修复1：统一转换为本地时区（解决UTC时区导致的时间差）
        now = timezone.localtime()  # 替换原有的 datetime.now()
        arrival_time = timezone.localtime(arrival_time)
        
        # 修复2：忽略秒级精度（前端只选到分钟，后端可能带秒导致误判）
        now = now.replace(second=0, microsecond=0)
        arrival_time = arrival_time.replace(second=0, microsecond=0)
        
        # 验证逻辑
        if arrival_time < now:
            raise ValidationError(f"预约时间不能早于当前时间（当前时间：{now.strftime('%Y-%m-%d %H:%M')}）")
        
        if arrival_time > now + timedelta(days=7):
            raise ValidationError(f"最多只能预约未来7天的号源（最晚：{(now + timedelta(days=7)).strftime('%Y-%m-%d %H:%M')}）")
        
        return arrival_time

# 缴费表单
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['total_amount', 'medical_insurance', 'pay_method']
        widgets = {
            # 为金额输入框添加form-control类
            'total_amount': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'class': 'form-control'
                }
            ),
            # 为医保金额输入框添加form-control类
            'medical_insurance': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'class': 'form-control'
                }
            ),
            # 为支付方式选择框添加form-select类
            'pay_method': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_amount')
        insurance = cleaned_data.get('medical_insurance')
        if insurance and total and insurance > total:
            raise ValidationError("医保金额不能超过总金额")
        return cleaned_data

# 排班表单
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['doctor', 'room', 'schedule_date', 'time_slot', 'status']
        widgets = {
            # 为医生选择框添加form-select类
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            # 为诊室选择框添加form-select类
            'room': forms.Select(attrs={'class': 'form-select'}),
            # 为日期输入框添加form-control类
            'schedule_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            # 为时间段选择框添加form-select类
            'time_slot': forms.Select(attrs={'class': 'form-select'}),
            # 为状态选择框添加form-select类
            'status': forms.Select(attrs={'class': 'form-select'}),
        }