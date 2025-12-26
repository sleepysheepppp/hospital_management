from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from decimal import Decimal  # 适配DecimalField
from clinic.models import (
    Department, ClinicRoom, Doctor, Patient,
    Schedule, Appointment, MedicalRecord, Payment
)

class Command(BaseCommand):
    help = '一次性填充门诊管理系统的测试数据（匹配最终版models.py）'

    def handle(self, *args, **options):
        # 1. 清空现有数据（避免重复/冲突）
        self.stdout.write('正在清空旧数据...')
        # 按外键依赖顺序删除（从子表到父表）
        Payment.objects.all().delete()
        MedicalRecord.objects.all().delete()
        Appointment.objects.all().delete()
        Schedule.objects.all().delete()
        Doctor.objects.all().delete()  # Doctor关联User，先删Doctor再删User
        Patient.objects.all().delete()
        ClinicRoom.objects.all().delete()
        Department.objects.all().delete()
        # 删除测试创建的用户（保留超级管理员）
        User.objects.filter(username__in=['doctor1', 'doctor2', 'doctor3', 'reception', 'patient1', 'patient2']).delete()

        # 2. 创建科室（匹配Department模型）
        self.stdout.write('正在创建科室...')
        dept1 = Department.objects.create(
            dept_name='内科',
            dept_desc='普通内科诊疗，涵盖呼吸、消化、心血管内科常见疾病'
        )
        dept2 = Department.objects.create(
            dept_name='外科',
            dept_desc='普通外科诊疗，涵盖骨科、普外科、泌尿外科常见疾病'
        )
        dept3 = Department.objects.create(
            dept_name='儿科',
            dept_desc='儿童常见疾病诊疗，0-14岁儿童内科/外科基础诊疗'
        )

        # 3. 创建诊室（匹配ClinicRoom模型：room_id(主键)、dept、location）
        self.stdout.write('正在创建诊室...')
        room1 = ClinicRoom.objects.create(
            room_id='101',
            dept=dept1,
            location='1楼101室'
        )
        room2 = ClinicRoom.objects.create(
            room_id='102',
            dept=dept1,
            location='1楼102室'
        )
        room3 = ClinicRoom.objects.create(
            room_id='201',
            dept=dept2,
            location='2楼201室'
        )
        room4 = ClinicRoom.objects.create(
            room_id='301',
            dept=dept3,
            location='3楼301室'
        )

        # 4. 创建医生（关键：Doctor关联User，先创建User再关联）
        self.stdout.write('正在创建医生...')
        # 医生1：张三（内科）
        doctor_user1 = User.objects.create_user(
            username='doctor1',
            password='123456',
            email='doctor1@test.com'
        )
        doctor1 = Doctor.objects.create(
            user=doctor_user1,
            name='张三',
            dept=dept1,
            title='主治医师',
            mobile='13800138000',  # 符合手机号验证规则
            work_status='在职'
        )
        # 医生2：李四（外科）
        doctor_user2 = User.objects.create_user(
            username='doctor2',
            password='123456',
            email='doctor2@test.com'
        )
        doctor2 = Doctor.objects.create(
            user=doctor_user2,
            name='李四',
            dept=dept2,
            title='副主任医师',
            mobile='13900139000',
            work_status='在职'
        )
        # 医生3：王五（儿科）
        doctor_user3 = User.objects.create_user(
            username='doctor3',
            password='123456',
            email='doctor3@test.com'
        )
        doctor3 = Doctor.objects.create(
            user=doctor_user3,
            name='王五',
            dept=dept3,
            title='医师',
            mobile='13700137000',
            work_status='在职'
        )

        # 5. 创建测试用户（前台、患者）
        self.stdout.write('正在创建测试用户...')
        # 前台用户（staff=True, is_superuser=False）
        reception_user = User.objects.create_user(
            username='reception',
            password='123456',
            email='reception@test.com'
        )
        reception_user.is_staff = True
        reception_user.save()

        # 患者用户1：小明
        patient_user1 = User.objects.create_user(
            username='patient1',
            password='123456',
            email='patient1@test.com'
        )
        patient1 = Patient.objects.create(
            user=patient_user1,
            name='小明',
            gender='男',
            id_card='110101199001011234',  # 唯一身份证号
            mobile='13600136000',
            birth_date='1990-01-01'
        )

        # 患者用户2：小红
        patient_user2 = User.objects.create_user(
            username='patient2',
            password='123456',
            email='patient2@test.com'
        )
        patient2 = Patient.objects.create(
            user=patient_user2,
            name='小红',
            gender='女',
            id_card='110101199502021234',  # 唯一身份证号
            mobile='13500135000',
            birth_date='1995-02-02'
        )

        # 6. 创建排班（匹配Schedule模型）
        self.stdout.write('正在创建排班...')
        Schedule.objects.create(
            doctor=doctor1,
            room=room1,
            schedule_date=datetime.now().date(),
            time_slot='上午（8:00-12:00）',
            status=1  # 可接诊
        )
        Schedule.objects.create(
            doctor=doctor2,
            room=room3,
            schedule_date=datetime.now().date(),
            time_slot='下午（14:00-18:00）',
            status=1
        )

        # 7. 创建预约（匹配Appointment模型，避免unique_together冲突）
        self.stdout.write('正在创建预约...')
        appt1 = Appointment.objects.create(
            patient=patient1,
            dept=dept1,
            appt_time=datetime.now() - timedelta(hours=2),
            arrival_time=datetime.now() - timedelta(hours=1),
            status=1  # 已完成
        )
        appt2 = Appointment.objects.create(
            patient=patient2,
            dept=dept2,
            appt_time=datetime.now() - timedelta(hours=3),
            arrival_time=datetime.now() - timedelta(hours=2),
            status=1  # 已完成
        )

        # 8. 创建就诊记录（匹配MedicalRecord模型：新增symptom、prescription、appointment）
        self.stdout.write('正在创建就诊记录...')
        record1 = MedicalRecord.objects.create(
            patient=patient1,
            doctor=doctor1,
            room=room1,
            visit_time=datetime.now() - timedelta(hours=1),
            visit_status=1,  # 已离院
            symptom='咳嗽、发烧3天，体温38.5℃',  # 病情描述
            prescription='布洛芬缓释胶囊 1粒/次，3次/日；阿莫西林胶囊 2粒/次，2次/日',  # 处方
            appointment=appt1  # 关联预约
        )
        record2 = MedicalRecord.objects.create(
            patient=patient2,
            doctor=doctor2,
            room=room3,
            visit_time=datetime.now() - timedelta(hours=2),
            visit_status=1,  # 已离院
            symptom='腹痛、腹泻1天，无发热',
            prescription='蒙脱石散 1袋/次，3次/日；口服补液盐 500ml/日',
            appointment=appt2
        )

        # 9. 创建缴费记录（匹配Payment模型：DecimalField，self_pay自动计算）
        self.stdout.write('正在创建缴费记录...')
        Payment.objects.create(
            record=record1,
            total_amount=Decimal('150.00'),  # Decimal类型适配DecimalField
            medical_insurance=Decimal('80.00'),
            # self_pay自动计算，无需手动赋值
            pay_method='微信'
        )
        Payment.objects.create(
            record=record2,
            total_amount=Decimal('200.00'),
            medical_insurance=Decimal('100.00'),
            pay_method='支付宝'
        )

        # 完成提示
        self.stdout.write(self.style.SUCCESS('✅ 测试数据填充完成！'))
        self.stdout.write('\n📌 测试账号信息：')
        self.stdout.write('  超级管理员：admin / 你设置的密码（createsuperuser时输入）')
        self.stdout.write('  前台用户：reception / 123456')
        self.stdout.write('  患者用户1：patient1 / 123456')
        self.stdout.write('  患者用户2：patient2 / 123456')
        self.stdout.write('  医生用户1：doctor1 / 123456（张三/内科）')
        self.stdout.write('  医生用户2：doctor2 / 123456（李四/外科）')