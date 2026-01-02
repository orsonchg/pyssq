from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.conf import settings
from django.contrib import messages

from ai_models.forms.features import SsqFeatureSetForm
from ssq.models import SsqDraw
from ai_models.models import SsqFeatureSet

from utils.paginations import Bootstrap5Pagination


def features_list(request):
    features_obj = SsqFeatureSet.objects.all().order_by('-created_at')

    all_count = features_obj.count()
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

    context = {
        'features': features_obj[pager.page_slice],
        'pager': pager,
        'all_count': all_count,
        'per_page': per_page,
    }

    return render(request, 'ai_models/features_list.html', context)


def features_create(request):
    """
    模型特征新增
    :param request:
    :return:
    """
    if request.method == 'POST':
        form = SsqFeatureSetForm(request.POST)
        if form.is_valid():
            f_obj = form.save(commit=False)

            # 检查开奖记录
            draws = SsqDraw.objects.filter(
                period__gte=f_obj.period_start,
                period__lte=f_obj.period_end
            ).order_by('period')
            if not draws:
                raise ValueError(f'在期号范围 {f_obj.period_start}-{f_obj.period_end} 内没有找到开奖记录')

            # 定义特征列和目标列
            f_obj.feature_columns = [
                'red_sum', 'red_span', 'red_ac_value', 'red_tail_sum','red_odd_count', 'red_even_count',
                'red_prime_count','zone_1_count', 'zone_2_count', 'zone_3_count','weekday', 'month', 'quarter'
            ]
            f_obj.target_columns = ['next_red_sum', 'next_red_ac_value' 'next_red_odd_count', 'next_red_even_count',
                                    'next_red_prime_count','next_blue_ball']
            f_obj.sample_count = max(0, draws.count() - 1)
            f_obj.save()

            messages.success(request, '特征集生成成功！')
            return redirect(reverse('ai_models:features_list'))
        else:
            error_msg = f"表单验证失败：{form.errors}"
            messages.error(request, f'表单验证错误！{error_msg}')
    else:
        form = SsqFeatureSetForm()
    return render(request, 'change.html', {'form': form})


def features_delete(request, pk):
    """
    模型特征删除
    :param request:
    :param pk:
    :return:
    """
    features_obj = get_object_or_404(SsqFeatureSet, pk=pk)

    base_list_url = reverse('ai_models:features_list')
    if request.method == 'GET':
        return render(request, 'alert.html', {'cancel': base_list_url})
    features_obj.delete()
    return redirect(base_list_url)


def features_detail(request, pk):
    """
    模型特征详情
    :param request:
    :param pk:
    :return:
    """
    feature_set = get_object_or_404(SsqFeatureSet, pk=pk)

    total_samples = feature_set.sample_count

    # 获取相关双色球开奖记录
    draws = SsqDraw.objects.filter(
        period__gte=feature_set.period_start,
        period__lte=feature_set.period_end
    ).order_by('period')

    # 生成记录
    preview_data = []
    if len(draws) >= 2:
        for i in range(min(20, len(draws) - 1)):
            current = draws[i]
            next_draw = draws[i + 1]

            features = {
                'period': current.period,
                'red_sum': current.red_sum,
                'red_span': current.red_span,
                'red_ac_value': current.red_ac_value,
                'red_odd_count': current.red_odd_count,
                'red_even_count': current.red_even_count,
                'red_prime_count': current.red_prime_count,
                'red_tail_sum': current.red_tail_sum,
                'zone_1': current.red_zones[0] if current.red_zones else 0,
                'zone_2': current.red_zones[1] if len(current.red_zones) > 1 else 0,
                'zone_3': current.red_zones[2] if len(current.red_zones) > 2 else 0,
            }

            targets = {
                'next_period': next_draw.period,
                'next_red_sum': next_draw.red_sum,
                'next_red_ac_value': next_draw.red_ac_value,
                'next_red_odd_count': next_draw.red_odd_count,
                'next_red_even_count': next_draw.red_even_count,
                'next_red_prime_count': next_draw.red_even_count,
                'next_blue_ball': next_draw.blue_ball,
            }
            preview_data.append({
                'features': features,
                'targets': targets,
            })


    context = {
        'feature_set': feature_set,
        'total_samples': total_samples,
        'sample_list': preview_data,
    }
    return render(request, 'ai_models/features_detail.html', context)


