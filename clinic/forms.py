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
            'arrival_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def clean_arrival_time(self):
        arrival_time = self.cleaned_data['arrival_time']
        # 验证预约时间不能早于当前时间
        if arrival_time < datetime.now():
            raise ValidationError("预约时间不能早于当前时间")
        # 验证预约时间需在未来7天内
        if arrival_time > datetime.now() + timedelta(days=7):
            raise ValidationError("最多只能预约未来7天的号源")
        return arrival_time

# 缴费表单
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['total_amount', 'medical_insurance', 'pay_method']
        widgets = {
            'total_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'medical_insurance': forms.NumberInput(attrs={'step': '0.01'}),
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
            'schedule_date': forms.DateInput(attrs={'type': 'date'}),
        }