from django import forms
from django.forms import (
    CheckboxInput, RadioSelect, FileInput, Textarea,
    Select, SelectMultiple, DateInput, DateTimeInput, TimeInput
)

class Bootstrap5FormMixin:
    """
    安全版 Bootstrap5 Form Mixin
    - 适配Bootstrap5的表单类名和组件特性
    - 初始化时不访问 errors
    - BoundField 在模板中判断错误
    """

    bootstrap_class_exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in getattr(self, 'bootstrap_class_exclude', []):
                continue

            widget = field.widget
            bound_field = self[name]  # BoundField，可在模板访问

            # 必填字段标记
            bound_field.is_required = field.required

            # 日期控件 - bootstrap5 日期格式选择器
            if isinstance(widget, (DateInput, DateTimeInput, TimeInput)):
                self._add_class(widget, 'form-control datetimepicker-input')
                bound_field.is_datepicker = True
                # 添加data属性支持 bootstrap5日期插件
                widget.attrs.setdefault('data-bs-toggle', 'datetimepicker')
                if 'placeholder' not in widget.attrs:
                    widget.attrs['placeholder'] = f"请选择{field.label}"
            else:
                bound_field.is_datepicker = False

            # 多选 / Select2 下拉选择器 - 适配bootstrap5和Select2
            if isinstance(widget, (Select, SelectMultiple)):
                # bootstrap5原生下拉框类名 + Select2支持
                self._add_class(widget, 'form-select select2')
                bound_field.is_select2 = True
            else:
                bound_field.is_select2 = False

            # Checkbox / Radio 复选框和单选框 - bootstrap5使用form-check布局
            if isinstance(widget, CheckboxInput):
                self._add_class(widget, 'form-check-input')
                bound_field.is_checkbox = True
            elif isinstance(widget, RadioSelect):
                self._add_class(widget, 'form-check-input')
                bound_field.is_radio = True
            else:
                bound_field.is_checkbox = False
                bound_field.is_radio = False

            # File 文件上传控件 -- bootstrap5更名
            if isinstance(widget, FileInput):
                self._add_class(widget, 'form-control form-control-file')

            # Textarea / Input # 文本输入和文本域
            if isinstance(widget, (Textarea, forms.TextInput, forms.NumberInput,
                                   forms.EmailInput, forms.URLInput, forms.PasswordInput)):
                self._add_class(widget, 'form-control')
                if isinstance(widget, Textarea) and 'rows' not in widget.attrs:
                    widget.attrs['rows'] = 4

                # 添加表单控件焦点状态优化
                widget.attrs.setdefault('autocomplete', 'off')

            # 添加aria标签 提升可访问性
            widget.attrs.setdefault('aria-label', field.label or field.name)

            # placeholder
            if not widget.attrs.get('placeholder') and hasattr(field, 'label'):
                if 'placeholder' not in widget.attrs:
                    widget.attrs['placeholder'] = f"请输入{field.label}"

    # --------------------------
    # 工具函数
    # --------------------------
    def _add_class(self, widget, new_class):
        """添加类名时去重并保持顺序"""
        old_classes = widget.attrs.get('class', '').split()

        # 拆分新类名防止批量添加时候重复
        new_classes = new_class.split()
        for cls in new_classes:
            if cls not in old_classes:
                old_classes.append(cls)
        widget.attrs['class'] = ' '.join(old_classes)

