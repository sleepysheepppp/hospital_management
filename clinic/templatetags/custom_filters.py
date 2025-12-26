from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """自定义add_class过滤器：给Django表单字段添加CSS类"""
    return field.as_widget(attrs={"class": css_class})