from django.db import models

class SsqDraw(models.Model):
    """双色球开奖记录"""
    period = models.CharField('期号', max_length=20, unique=True, db_index=True)
    draw_date = models.DateField('开奖日期', db_index=True)
    red_balls = models.JSONField(verbose_name='红球', default=list)
    blue_ball = models.IntegerField('蓝球', default=0)

    # 统计字段
    red_sum = models.IntegerField('红球和值', default=0)
    red_odd_count = models.IntegerField('红球奇数个数', default=0)
    red_even_count = models.IntegerField('红球偶数个数', default=0)
    red_prime_count = models.IntegerField('红球质数个数', default=0)
    red_zones = models.JSONField(verbose_name='红球三区分布', default=list)

    # 衍生特征
    red_span = models.IntegerField('红球跨度', default=0)
    red_ac_value = models.IntegerField('红球AC值', default=0)
    red_tail_sum = models.IntegerField('红球尾数和', default=0)

    # 技术指标
    hot_numbers = models.JSONField(verbose_name='热号', default=list)
    cold_numbers = models.JSONField(verbose_name='冷号', default=list)

    # 增加缓存字段
    last_updated = models.DateTimeField('最后更新时间', auto_now=True)

    # 增加预测字段
    prediction_difficulty = models.FloatField(
        '预测难度系数',
        default=0.5,
        help_text='基于历史模式计算的预测难度，0-1之间'
    )
    # 增加开奖特征组
    feature_group = models.CharField(
        '特征组别',
        max_length=20,
        choices=[
            ('normal', '常规模式'),
            ('anomaly', '异常模式'),
            ('pattern', '规律模式'),
            ('random', '随机模式'),
        ],
        default='normal',
    )

    # 常亮定义（提升维护）
    PRIME_SET = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
    RED_BALL_RANGE = (1, 33)
    BLUE_BALL_RANGE = (1, 16)
    RED_BALL_COUNT = 6

    class Meta:
        verbose_name = '双色球开奖记录'
        verbose_name_plural = verbose_name
        ordering = ['-period']
        indexes = [models.Index(fields=['period']),
                   models.Index(fields=['draw_date']),
                   ]
        constraints = [models.UniqueConstraint(
            fields=['period', 'draw_date'],
            name='unique_period_date')
        ]

    def __str__(self):
        return f"第{self.period}期: {self.red_balls} + [{self.blue_ball}]"

    def save(self, *args, **kwargs):
        # 自动计算统计特征
        if self.red_balls and len(self.red_balls) == self.RED_BALL_COUNT:
            self._calculate_features()
        super().save(*args, **kwargs)

    def _calculate_features(self):
        """计算统计特征"""
        if self.red_balls:
            reds = sorted(self.red_balls)

            #基础统计
            self.red_sum = sum(reds)
            self.red_odd_count = sum(1 for n in reds if n % 2 == 1)
            self.red_even_count = self.RED_BALL_COUNT - self.red_odd_count

            # 质数判断
            self.red_prime_count = sum(1 for n in reds if n in self.PRIME_SET)

            # 三区分布
            zone1 = sum(1 for n in reds if 1 <= n <= 11)
            zone2 = sum(1 for n in reds if 12 <= n <= 22)
            zone3 = sum(1 for n in reds if 23 <= n <= 33)
            self.red_zones = [zone1, zone2, zone3]

            # 跨度
            self.red_span = reds[-1] - reds[0] if reds else 0

            # 尾数和
            self.red_tail_sum = sum(n % 10 for n in reds)

            # AC值计算
            self.red_ac_value = self._calculate_ac_value(reds)

    def _calculate_ac_value(self, reds):
        """计算AC值： AC = 组合数 - （最大值-最小值）+ 1 - 重复数（双色球无重复，重复数为0）"""
        if len(reds) < 2:
            return 0
        # 计算两两差值的个数（去重）
        diffs = set()
        for i in range(len(reds)):
            for j in range(i + 1, len(reds)):
                diffs.add(reds[j] - reds[i])
        combination_count = len(diffs)
        ac_value = combination_count - (reds[-1] - reds[0]) + 1
        return max(ac_value, 0)