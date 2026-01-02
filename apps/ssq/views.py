from django.shortcuts import render,redirect, get_object_or_404, reverse
from django.contrib import messages
from django.conf import settings
from ssq.models import SsqDraw
from ssq.forms import SsqDrawForm
from utils.paginations import Bootstrap5Pagination


def ssq_list(request):
    """
    双色球列表
    :param request:
    :return:
    """
    form = SsqDrawForm()
    ssq_objs = SsqDraw.objects.all().order_by('-period')

    all_count = ssq_objs.count()
    base_url = request.path_info
    current_page = request.GET.get('page', 1)
    query_params = request.GET.copy()
    per_page = settings.PAGE_SIZE

    pager = Bootstrap5Pagination(
        current_page=current_page,
        all_count=all_count,
        base_url=base_url,
        query_params=query_params,
        per_page=per_page,
        pager_page_count=7,
        show_info=True,
        size='sm',
        justify='center',
        aria_label='分页导航'
    )

    # 获取最新一期
    latest_ssq = SsqDraw.objects.order_by('-period').first()
    latest_period = latest_ssq.period if latest_ssq else None

    context = {
        'ssq_objs': ssq_objs[pager.page_slice],
        'pager': pager,
        'all_count': all_count,
        'per_page': per_page,
        'latest_period': latest_period,
        'form': form,
    }

    return render(request,'ssq/ssq_list.html',context)

def ssq_create(request):
    """
    双色球新增
    :param request:
    :return:
    """
    if request.method == 'POST':
        form = SsqDrawForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '双色球保存成功！')
            return redirect(reverse('ssq:ssq_list'))
        else:
            error_msg = f"表单验证失败：{form.errors}"
            messages.error(request, f'表单验证错误！{error_msg}')
    else:
        form = SsqDrawForm()
    return render(request, 'change.html', {'form': form})

def ssq_update(request, pk):
    """
    双色球编辑
    :param request:
    :param pk:
    :return:
    """
    ssq_obj = get_object_or_404(SsqDraw, pk=pk)
    if request.method == 'POST':
        form = SsqDrawForm(request.POST, instance=ssq_obj)
        if form.is_valid():
            form.save()
            messages.success(request, '双色球更新成功！')
            return redirect(reverse('ssq:ssq_list'))
        else:
            error_msg = f"表单验证失败：{form.errors}"
            messages.error(request, f'表单验证错误！{error_msg}')
    else:
        form = SsqDrawForm(instance=ssq_obj)
    return render(request, 'change.html', {'form': form})


def ssq_delete(request, pk):
    """
    双色球删除
    :param request:
    :param pk:
    :return:
    """
    pass


def ssq_detail(request, pk):
    """
    双色球详情
    :param request:
    :param pk:
    :return:
    """
    pass

