from django import forms
from .models import Patient, Appointment, Payment, Schedule
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

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
                    'required': True  # 前端强制必填
                }, 
                format='%Y-%m-%dT%H:%M'
            ),
        }
    # 给字段添加必填验证（后端兜底）
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dept'].required = True
        self.fields['arrival_time'].required = True

    def clean_arrival_time(self):
        arrival_time = self.cleaned_data.get('arrival_time')  # 用get避免KeyError
        # 先检查是否为空
        if not arrival_time:
            raise ValidationError("请选择预约时间")
        # 原有验证逻辑
        if arrival_time < datetime.now():
            raise ValidationError("预约时间不能早于当前时间")
        if arrival_time > datetime.now() + timedelta(days=7):
            raise ValidationError("最多只能预约未来7天的号源")
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