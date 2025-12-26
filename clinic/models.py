from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator

# 科室模型
class Department(models.Model):
    dept_id = models.AutoField(primary_key=True, verbose_name="科室ID")
    dept_name = models.CharField(max_length=50, unique=True, verbose_name="科室名称")
    dept_desc = models.CharField(max_length=200, blank=True, null=True, verbose_name="科室描述")

    def __str__(self):
        return self.dept_name

    class Meta:
        verbose_name = "科室"
        verbose_name_plural = "科室"

# 诊室模型
class ClinicRoom(models.Model):
    room_id = models.CharField(max_length=10, primary_key=True, verbose_name="诊室编号")
    dept = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="所属科室")
    location = models.CharField(max_length=50, verbose_name="诊室位置")

    def __str__(self):
        return f"{self.dept.dept_name}-{self.room_id}"

    class Meta:
        verbose_name = "诊室"
        verbose_name_plural = "诊室"

# 医生模型（关联Django内置User）
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="关联用户")
    name = models.CharField(max_length=20, verbose_name="医生姓名")
    dept = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="所属科室")
    title = models.CharField(max_length=20, verbose_name="职称")
    phone_regex = RegexValidator(regex=r'^1[3-9]\d{9}$', message="手机号格式错误")
    mobile = models.CharField(validators=[phone_regex], max_length=11, verbose_name="联系电话")
    work_status = models.CharField(max_length=10, choices=[('在职', '在职'), ('离职', '离职')], default='在职', verbose_name="工作状态")

    def __str__(self):
        return f"{self.name}({self.title})"

    class Meta:
        verbose_name = "医生"
        verbose_name_plural = "医生"

# 患者模型
class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True, verbose_name="患者ID")
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="关联用户")
    name = models.CharField(max_length=20, verbose_name="患者姓名")
    gender = models.CharField(max_length=2, choices=[('男', '男'), ('女', '女'), ('其他', '其他')], verbose_name="性别")
    id_card = models.CharField(max_length=18, unique=True, verbose_name="身份证号")
    phone_regex = RegexValidator(regex=r'^1[3-9]\d{9}$', message="手机号格式错误")
    mobile = models.CharField(validators=[phone_regex], max_length=11, verbose_name="联系电话")
    birth_date = models.DateField(verbose_name="出生日期")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "患者"
        verbose_name_plural = "患者"

# 排班模型
class Schedule(models.Model):
    schedule_id = models.AutoField(primary_key=True, verbose_name="排班ID")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="医生")
    room = models.ForeignKey(ClinicRoom, on_delete=models.CASCADE, verbose_name="诊室")
    schedule_date = models.DateField(verbose_name="排班日期")
    time_slot = models.CharField(max_length=20, verbose_name="接诊时间段")
    status = models.IntegerField(choices=[(0, '不可接诊'), (1, '可接诊')], default=1, verbose_name="排班状态")

    class Meta:
        verbose_name = "排班"
        verbose_name_plural = "排班"
        unique_together = ('doctor', 'schedule_date', 'time_slot')  # 避免重复排班

    def __str__(self):
        return f"{self.doctor.name}-{self.schedule_date}-{self.time_slot}"

# 预约模型
class Appointment(models.Model):
    appt_id = models.AutoField(primary_key=True, verbose_name="预约ID")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="患者")
    dept = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="预约科室")
    appt_time = models.DateTimeField(auto_now_add=True, verbose_name="预约时间")
    arrival_time = models.DateTimeField(verbose_name="预计到达时间")
    status = models.IntegerField(choices=[(0, '未就诊'), (1, '已完成'), (2, '已取消')], default=0, verbose_name="预约状态")

    class Meta:
        verbose_name = "预约"
        verbose_name_plural = "预约"
        unique_together = ('patient', 'arrival_time', 'dept')  # 避免重复预约

    def __str__(self):
        return f"{self.patient.name}-{self.arrival_time.strftime('%Y-%m-%d %H:%M')}"

# 就诊记录模型
class MedicalRecord(models.Model):
    record_id = models.AutoField(primary_key=True, verbose_name="就诊ID")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="患者")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="接诊医生")
    room = models.ForeignKey(ClinicRoom, on_delete=models.CASCADE, verbose_name="就诊诊室")
    visit_time = models.DateTimeField(auto_now_add=True, verbose_name="就诊时间")
    visit_status = models.IntegerField(choices=[(0, '就诊中'), (1, '已离院')], default=0, verbose_name="就诊状态")
    symptom = models.CharField(max_length=500, blank=True, null=True, verbose_name="病情描述")
    prescription = models.CharField(max_length=500, blank=True, null=True, verbose_name="处方信息")
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联预约")

    class Meta:
        verbose_name = "就诊记录"
        verbose_name_plural = "就诊记录"

    def __str__(self):
        return f"{self.patient.name}-{self.visit_time.strftime('%Y-%m-%d %H:%M')}"

# 缴费模型
class Payment(models.Model):
    pay_id = models.AutoField(primary_key=True, verbose_name="缴费ID")
    record = models.OneToOneField(MedicalRecord, on_delete=models.CASCADE, verbose_name="关联就诊记录")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="总金额")
    medical_insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="医保金额")
    self_pay = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="自费金额")
    pay_time = models.DateTimeField(auto_now_add=True, verbose_name="缴费时间")
    pay_method = models.CharField(max_length=10, choices=[('现金', '现金'), ('微信', '微信'), ('支付宝', '支付宝'), ('医保', '医保')], verbose_name="缴费方式")

    class Meta:
        verbose_name = "缴费记录"
        verbose_name_plural = "缴费记录"

    def save(self, *args, **kwargs):
        # 自动计算自费金额
        self.self_pay = self.total_amount - self.medical_insurance
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.record.patient.name}-{self.total_amount}元"