from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.conf import settings
from ssq.models import SsqDraw
from ssq.forms import SsqDrawForm
from utils.paginations import Bootstrap5Pagination

from collections import Counter


def ssq_list(request):
    """
    双色球列表
    :param request:
    :return:
    """
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
    }

    return render(request, 'ssq/ssq_list.html', context)


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


def ssq_detail(request, pk):
    """
    双色球详情
    :param request:
    :param period:
    :return:
    """
    ssq_obj = get_object_or_404(SsqDraw, pk=pk)
    period = ssq_obj.period if ssq_obj else None
    # 如果period是最新，重定向到最新一期
    if period == 'latest':
        # 仅仅查询period字段，减少数据传输
        latest_ssq = SsqDraw.objects.only('period').order_by('-period').first()
        if latest_ssq:
            return redirect('ssq:ssq_detail', pk=latest_ssq.period)
        # 无数据时重定向
        return redirect(reverse('ssq:ssq_list'))

        # ========== 2. 统一期数类型（关键：先转类型，避免后续ORM查询错误） ==========
    try:
        # 将URL传入的期数转为整数（匹配数据库period字段类型）
        period_int = int(period)
    except ValueError:
        # 非数字期数直接返回404
        return render(
            request,
            '404.html',
            {'message': f'期数格式错误：{period}，仅支持数字期数或latest'},
            status=404
        )

    # 获取当前开奖记录，增强容错
    try:
        ssq = SsqDraw.objects.only(
            'period', 'draw_date', 'red_balls', 'blue_ball', 'last_updated'
        ).get(period=period_int)
    except SsqDraw.DoesNotExist:
        # 期数不存在返回404
        return render(request, '404.html', {'message': f'未找到{period}期双色球开奖记录'}, status=404)

    # 一次性查询所有期数并排序
    all_periods = SsqDraw.objects.values_list('period', flat=True).order_by('-period')
    periods_list = list(all_periods)
    total_count = len(periods_list)

    # 计算当期期数的索引
    try:
        current_index = periods_list.index(period_int)
    except ValueError:
        # 当期数不存在，默认 -1
        current_index = -1

    # 获取前后期数
    prev_period = None
    next_period = None
    if current_index != -1:
        # 当前期数：当前索引+1
        if current_index + 1 < total_count:
            prev_period = periods_list[current_index + 1]

        # 后期数
        if current_index - 1 >= 0:
            next_period = periods_list[current_index - 1]

    # =====优化热号和冷号逻辑
    # 自定义统计范围
    HOT_NUMBERS_COUNT = 10  # 显示的热号数量
    COLD_NUMBERS_COUNT = 10 # 显示冷号数量
    RECENT_FOR_HOT = 30 # 热号统计最近期数
    RECENT_FOR_COLD = 20 # 冷号统计最近期数

    #获取历史数据
    history_draws = SsqDraw.objects.filter(period__lt=period_int)
    history_draws = history_draws.only('period', 'red_balls').order_by('-period')

    # 热号统计 最近50期 出现频率最高的红球
    recent_for_hot = history_draws[:RECENT_FOR_HOT]

    red_balls_counter = Counter()
    for draw in recent_for_hot:
        if isinstance(draw.red_balls, (list, tuple)):
            red_balls_counter.update(draw.red_balls)

    # 获取出现频率最高的号码，并带上出现次数的信息
    hot_number_with_count = red_balls_counter.most_common(HOT_NUMBERS_COUNT)
    hot_numbers = [num for num, count in hot_number_with_count]
    hot_numbers = sorted(hot_numbers)
    hot_numbers_info = [
        {
            'number': num,
            'count': count,
            'frequency': f'{count}/{RECENT_FOR_HOT}',
            'percentage': round(count/RECENT_FOR_HOT * 100, 1), # 添加百分比
        }
        for num, count in hot_number_with_count
    ]

    # 冷号统计，最近30期未出现的红球
    recent_for_cold = history_draws[:RECENT_FOR_COLD]

    # 收集最近30期出现的所有红球
    recent_numbers_set = set()

    for draw in recent_for_cold:
        if isinstance(draw.red_balls, (list, tuple)):
            recent_numbers_set.update(draw.red_balls)

    # 所有可能的红球号码[1-33]
    all_red_numbers = set(range(1, 34))
    # 冷号码
    cold_numbers_set = all_red_numbers - recent_numbers_set

    # 冷号处理，按缺失期数排序，缺失越久，越冷
    cold_numbers_info = []
    if cold_numbers_set:
        # 对于每个冷号，计算它已经多少期没有出现
        for number in sorted(cold_numbers_set):
            # 找到这个号码最后一次出现的期数
            last_appear = None
            for draw in history_draws:
                if isinstance(draw.red_balls, (list, tuple)) and number in draw.red_balls:
                    last_appear = draw.period
                    break

            if last_appear:
                # 计算缺失期数
                missing_periods = period_int - int(last_appear)
                cold_numbers_info.append(
                    {
                        'number': number,
                        'missing_periods': missing_periods,
                        'last_appear': last_appear,
                    }
                )
            else:
                # 如果从未出现过
                cold_numbers_info.append({
                    'number': number,
                    'missing_periods': period_int,
                    'last_appear': '从未出现',
                })
        #按照缺失期数降序排序，缺失越久越靠前
        cold_numbers_info.sort(key=lambda x: x['missing_periods'], reverse=True)

        # 只取N个最冷号码
        cold_numbers_info = cold_numbers_info[:COLD_NUMBERS_COUNT]
        cold_numbers = [info['number'] for info in cold_numbers_info]
    else:
        cold_numbers = []
        cold_numbers_info = []

    # 获取相似期数（红球相似度高的）
    similar_draws = []
    try:
        # 防呆：确保当前红球数据有效,计算当前红球集合
        current_reds = set(ssq.red_balls) if isinstance(ssq.red_balls, (list, tuple)) else set()
        if current_reds:
            raise ValueError("当前红球数据为空")

        # 获取其他50期数（排除当前期数）
        other_draws = SsqDraw.objects.filter(period__lt=period_int) # 只对历史期数
        other_draws = other_draws.exclude(period=period).only(
            'period', 'draw_date', 'red_balls', 'blue_ball'
        ).order_by('-period')[:50]

        for draw in other_draws:
            # 计算相似的(共同号码数)
            other_reds = set(draw.red_balls) if isinstance(draw.red_balls, (list, tuple)) else set()
            if not other_reds:
                continue  # 跳过红球数据异常
            # 计算共同号码数和相似度（避免除0）
            common_count = len(current_reds.intersection(other_reds))
            similarity = int((common_count / 6) * 100)

            # 帅选相似度超过50% 只显示相似度较高的
            if similarity >= 50:
                similar_draws.append({
                    'period': draw.period,
                    'draw_date': draw.draw_date,
                    'red_balls': draw.red_balls,
                    'blue_ball': draw.blue_ball,
                    'similarity': similarity,
                    'common_count': common_count,
                })
        # 按照相似度降序排序，取前10条
        similar_draws = sorted(similar_draws, key=lambda x: x['similarity'], reverse=True)[:10]
    except Exception as e:
        # 出错时，使用空列表
        similar_draws = []

    context = {
        'latest_period': periods_list[0] if periods_list else None,  # 优化：从列表取，避免重复查询
        'title': f'{period_int}期 双色球详情',
        'ssq': ssq,
        'hot_numbers': hot_numbers or [],
        'hot_numbers_info': hot_numbers_info,
        'cold_numbers': cold_numbers or [],
        'cold_numbers_info': cold_numbers_info,
        'prev_period': prev_period,
        'next_period': next_period,
        'current_index': current_index,
        'total_count': total_count,
        'current_serial_number': total_count - current_index if current_index != -1 else 0,
        'similar_draws': similar_draws,
        'periods_list': periods_list[:20],  # 最近20期
        'current_period': period_int,
        'hot_start_range': RECENT_FOR_HOT,
        'cold_start_range': RECENT_FOR_COLD,

    }

    return render(request, 'ssq/ssq_detail.html', context)
