from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import EmailValidator, RegexValidator
from accounts.models import UserInfo
from utils.bootstrap5 import Bootstrap5FormMixin

class CustomAuthenticationForm(Bootstrap5FormMixin, AuthenticationForm):
    """自定义登录表单"""
    username = forms.CharField(
        label='用户名或邮箱',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入用户名或邮箱',
            'autofocus': True
        })
    )

    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入密码'
        })
    )

    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'custom-control-input'
        }),
        label='记住我'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = '用户名或邮箱'


class CustomUserCreationForm(UserCreationForm):
    """自定义用户注册表单"""
    email = forms.EmailField(
        label='邮箱地址',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入邮箱地址',
            'required': True
        }),
        validators=[EmailValidator(message='请输入有效的邮箱地址')]
    )

    username = forms.CharField(
        label='用户名',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入用户名',
            'required': True
        }),
        max_length=30,
        min_length=3,
        help_text='用户名必须是3-30个字符，只能包含字母、数字和下划线'
    )

    phone = forms.CharField(
        label='手机号',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入手机号（可选）'
        }),
        validators=[RegexValidator(
            regex=r'^1[3-9]\d{9}$',
            message='请输入有效的手机号'
        )]
    )

    password1 = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入密码',
            'required': True
        }),
        help_text='密码必须至少8个字符，包含字母和数字'
    )

    password2 = forms.CharField(
        label='确认密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请再次输入密码',
            'required': True
        })
    )

    agree_terms = forms.BooleanField(
        label='我同意用户协议和隐私政策',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'custom-control-input'
        })
    )

    class Meta:
        model = UserInfo
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data['username']
        if not username.isalnum() and '_' not in username:
            raise forms.ValidationError('用户名只能包含字母、数字和下划线')
        if UserInfo.objects.filter(username=username).exists():
            raise forms.ValidationError('该用户名已被注册')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if UserInfo.objects.filter(email=email).exists():
            raise forms.ValidationError('该邮箱已被注册')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('两次输入的密码不一致')

        return cleaned_data



