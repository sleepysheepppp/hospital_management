from django import template

register = template.Library()

# 除法过滤器：处理浮点数除法，避免除0错误
@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0.0

# 乘法过滤器：处理浮点数乘法
@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0.0