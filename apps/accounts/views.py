import re
import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.http import JsonResponse
from django.contrib import messages
from accounts.forms import CustomAuthenticationForm,CustomUserCreationForm
from accounts.models import UserInfo, UserLoginHistory
from utils.paginations import Bootstrap5Pagination
from accounts.utils.login_security import is_locked, increase_fail, reset_fail, remaining_attempts

@login_required
def dashboard(request):
    return render(request, 'base.html')

def get_client_ip(request):
    """
    获取客户端真实IP
    :param request:
    :param HttpRequest:
    :return:
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')

    # 过滤内网IP
    private_ips = ['127.0.0.1', 'localhost', '::1']
    return ip if ip not in private_ips else '127.0.0.1'

def get_device_info(request):
    """
    获取用户设备信息
    :param request:
    :param HttpRequest:
    :return:
    """
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')

    #简单的设备判断
    if re.search(r'Mobile|Android|iPhone|iPad|iPod', user_agent, re.I):
        device_type = 'Mobile'
    elif re.search(r'Tablet|iPad', user_agent, re.I):
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'

        # 提取浏览器信息
    browser_match = re.search(r'(Chrome|Firefox|Safari|Edge|Opera)/\d+', user_agent, re.I)
    browser = browser_match.group(0) if browser_match else 'Unknown'

    return f"{device_type} - {browser}"

def index(request):
    return render(request, 'index.html')

def login_view(request):
    """
    登录
    :param request:
    :return:
    """
    ip = get_client_ip(request)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # 已登录处理
    if request.user.is_authenticated:
        if is_ajax:
            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('accounts:dashboard')
            })
        return redirect('accounts:dashboard')

    # ================= Ajax 登录 =================
    if request.method == 'POST' and is_ajax:
        try:
            data = json.loads(request.body.decode())
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            remember_me = data.get('remember_me', False)

            if not username or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': '用户名和密码不能为空'
                }, status=400)

            # 防爆破
            if is_locked(ip, username):
                return JsonResponse({
                    'status': 'error',
                    'message': '登录失败次数过多，请15分钟后再试'
                }, status=429)

            # 邮箱 → 用户名
            login_username = username
            if '@' in username:
                user_obj = UserInfo.objects.filter(email=username).first()
                if user_obj:
                    login_username = user_obj.username

            user = authenticate(
                request,
                username=login_username,
                password=password
            )

            if not user:
                increase_fail(ip, username)
                return JsonResponse({
                    'status': 'error',
                    'message': f'用户名或密码错误，还剩 {remaining_attempts(ip, username)} 次机会'
                }, status=400)

            login(request, user)
            reset_fail(ip, username)

            request.session.set_expiry(
                60 * 60 * 24 * 7 if remember_me else 0
            )

            return JsonResponse({
                'status': 'success',
                'message': f'欢迎回来，{user.username}!',
                'redirect_url': request.GET.get('next') or reverse('accounts:dashboard')
            })

        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': '服务器内部错误'
            }, status=500)

    # ================= 普通表单登录 =================
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            remember_me = form.cleaned_data.get('remember_me', False)
            request.session.set_expiry(
                60 * 60 * 24 * 7 if remember_me else 0
            )

            messages.success(request, f'欢迎回来，{user.username}')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, '用户名或密码错误')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'title': '用户登录'
    })

def logout_view(request):
    """
    登出
    :param request:
    :return:
    """
    pass

def register(request):
    """
    用户注册
    :param request:
    :return:
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # 保存用户
                user = form.save()

                # 直接登录用户，不需要重新认证
                login(request, user)

                # 判断是否为 AJAX 请求
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': '注册成功',
                        'redirect_url': '/accounts/dashboard/'
                    })
                else:
                    messages.success(request, '注册成功，欢迎加入我们！')
                    return redirect('accounts:dashboard')

            except Exception as e:
                error_msg = f'注册过程出错：{str(e)}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': error_msg
                    }, status=500)
                else:
                    messages.error(request, error_msg)
        else:
            # 收集表单错误信息
            error_messages = {}
            for field, errors in form.errors.items():
                # 格式化字段名，去掉下划线
                field_name = field.replace('_', ' ')
                error_messages[field] = [str(error) for error in errors]

            # 添加全局错误
            if form.non_field_errors():
                error_messages['__all__'] = [str(error) for error in form.non_field_errors()]

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': '表单验证失败',
                    'errors': error_messages
                }, status=400)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')

        # GET 请求或非 AJAX 提交失败，返回页面
    form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {
        'form': form,
        'title': '用户注册'
    })