from django import forms
from ssq.models import SsqDraw
from utils.bootstrap5 import Bootstrap5FormMixin

class SsqDrawForm(Bootstrap5FormMixin, forms.ModelForm):
    """
    双色球Form
    """

    red_balls = forms.CharField(
        label = '红球',
        required = True,
        help_text='请输入6个红球号码，用逗号分隔（例如：1,2,3,4,5,6）',
        error_messages = {
            'required': '红球不能为空',
            'blank': '红球不能为空'
        }
    )

    class Meta:
        model = SsqDraw
        fields = ['period', 'draw_date', 'red_balls', 'blue_ball']


    def clean_period(self):
        period = self.cleaned_data.get('period','').strip()

        # 期号不能为空
        if not period:
            raise forms.ValidationError('期号不能为空')

        exists = SsqDraw.objects.filter(period=period).exclude(pk=self.instance.pk).exists()
        if exists:
            raise forms.ValidationError(f'该期号{period}已经存在')
        return period


    def clean_red_balls(self):
        """验证红球输入格式"""
        data = self.cleaned_data['red_balls']
        try:
            # 将字符串转为列表
            numbers = [int(num.strip()) for num in data.split(',') if num.strip()]
            #验证数量
            if len(numbers) != self.Meta.model.RED_BALL_COUNT:
                raise forms.ValidationError(f'红球数量必须是{self.Meta.model.RED_BALL_COUNT}个号码')

            # 验证范围
            for num in numbers:
                if not(self.Meta.model.RED_BALL_RANGE[0] <= num <= self.Meta.model.RED_BALL_RANGE[1]):
                    raise forms.ValidationError(f'红球号码必须在{self.Meta.model.RED_BALL_RANGE}之间')
            # 验证是否重复
            if len(set(numbers)) != len(numbers):
                raise forms.ValidationError(f'红球号码不能重复')

            return sorted(numbers)
        except ValueError:
            raise forms.ValidationError('请输入有效的数字，用逗号分隔')

    def clean_blue_ball(self):
        """验证蓝球"""
        blue_ball = self.cleaned_data['blue_ball']
        if not (self.Meta.model.BLUE_BALL_RANGE[0] <= blue_ball <= self.Meta.model.BLUE_BALL_RANGE[1]):
            raise forms.ValidationError(f'蓝球必须在{self.Meta.model.BLUE_BALL_RANGE}之间')
        return blue_ball