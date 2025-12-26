// 通用提示框关闭
document.addEventListener('DOMContentLoaded', function() {
    // 3秒后自动关闭提示框
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 3000);
    });
});

// 表单验证增强
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const requiredInputs = this.querySelectorAll('[required]');
        let isValid = true;
        
        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('is-invalid');
                // 添加错误提示
                if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('invalid-feedback')) {
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = '此字段为必填项';
                    input.parentNode.appendChild(feedback);
                }
            } else {
                input.classList.remove('is-invalid');
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            e.stopPropagation();
        }
    });
});

// 输入框实时验证
document.querySelectorAll('input, select').forEach(element => {
    element.addEventListener('input', function() {
        if (this.hasAttribute('required') && this.value.trim()) {
            this.classList.remove('is-invalid');
        }
    });
});