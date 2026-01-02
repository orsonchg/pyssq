import hashlib

from django.db import models
from django.core.validators import MinLengthValidator

# Create your models here.
class SsqFeatureSet(models.Model):
    """特征数据集，直接训练出数据"""
    name = models.CharField('特征集名称', max_length=100,
                            validators=[MinLengthValidator(1, '特征集名称不能为空')], db_index=True)
    description = models.TextField('描述', blank=True, null=True)
    feature_columns = models.JSONField('特征列', default=list)
    target_columns = models.JSONField('目标列', default=list)
    period_start = models.CharField('开始期号', max_length=20, db_index=True)
    period_end = models.CharField('结束期号', max_length=20, db_index=True)
    sample_count = models.IntegerField('样本数量', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'ssq_features'
        verbose_name = '特征数据集'
        verbose_name_plural = verbose_name
        ordering = ['-created_at'] # 默认按创建时间倒序
        indexes = [
            models.Index(fields=['period_start', 'period_end'], name='idx_period_start_end'),
                   ]
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'period_start', 'period_end'],
                name='unique_feature_name_period',
                violation_error_message='相同名称+时间范围的特征集已存在'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.period_start}-{self.period_end})"

    def save(self, *args, **kwargs):
        """重写保存方法，确保样本数量非负数"""
        if self.sample_count < 0:
            self.sample_count = 0
        super().save(*args, **kwargs)


class SsqModel(models.Model):
    """训练好的模型"""
    MODEL_TYPES = [
        ('RF', 'Random Forest'),
        ('LGB', 'LightGBM'),
        ('XGB', 'XGBoost'),
        ('NN', 'Neural Network'),
        ('Transformer', 'Transformer'),
        ('Ensemble', 'Ensemble'), # 多模型 Ensemble 投票（RF + LGB + XGB）
    ]

    name = models.CharField('模型名称', max_length=100, db_index=True)
    model_type = models.CharField('模型类型', max_length=20, choices=MODEL_TYPES)
    version = models.CharField('版本号', max_length=20, default='1.0')

    # 新增字段用于Ensemble模型
    ensemble_models = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='ensemble_components',
        verbose_name='集成组件模型',
        limit_choices_to={'is_active': True}, #仅显示激活的模型
    )
    ensemble_weights = models.JSONField(
        '集成权重',
        default=list,
        blank=True,
        help_text='各子模型的权重列表，如[0.4, 0.3, 0.3]'
    )

    # 新增字段用于Transformer模型
    transformer_config = models.JSONField(
        'Transformer配置',
        default=dict,
        blank=True,
        help_text='Transformer模型超参数配置'
    )

    # 训练信息
    feature_set = models.ForeignKey(SsqFeatureSet, on_delete=models.PROTECT,
                                    related_name='models', verbose_name='关联特征集')
    train_period_start = models.CharField('训练开始期号', max_length=20, db_index=True)
    train_period_end = models.CharField('训练结束期号', max_length=20, db_index=True)

    # 性能指标
    train_score = models.FloatField('训练分数', null=True, blank=True)
    val_score = models.FloatField('验证分数', null=True, blank=True)
    test_score = models.FloatField('测试分数', null=True, blank=True)
    metrics = models.JSONField('评估指标', default=dict, blank=True)

    # 模型文件
    model_file = models.FileField('模型文件', upload_to='models/%Y/%m/%d/', help_text='支持.pkl/.h5/.pt格式')
    config_file = models.FileField('配置文件', upload_to='configs/%Y/%m/%d/',
                                   null=True, blank=True)

    # 防重复 (核心)
    model_hash = models.CharField('模型文件Hash', max_length=64,unique=True, editable=False)

    # 特征重要性
    feature_importance = models.JSONField('特征重要性', default=dict, blank=True)
    parameters = models.JSONField('模型参数', default=dict, blank=True)

    # 状态
    is_active = models.BooleanField('是否激活', default=True, db_index=True)

    # ========== 新增：双色球专用字段 ==========
    red_ball_range = models.JSONField(
        '红球范围',
        default=[1, 33],
        help_text='红球号码范围，如[1, 33]'
    )
    blue_ball_range = models.JSONField(
        '蓝球范围',
        default=[1, 16],
        help_text='蓝球号码范围，如[1, 16]'
    )
    red_ball_metrics = models.JSONField(
        '红球评估指标',
        default=dict,
        blank=True,
        help_text='红球相关的评估指标'
    )
    blue_ball_metrics = models.JSONField(
        '蓝球评估指标',
        default=dict,
        blank=True,
        help_text='蓝球相关的评估指标'
    )

    # 元数据
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'ssq_models'
        ordering = ['-created_at']
        verbose_name = '预测模型'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'version'],
                name = 'uniq_model_name_version'
            )
        ]

    def __str__(self):
        return f"{self.name} v{self.version} ({self.model_type})"

    def calculate_file_hash(self):
        """计算模型文件的MD5哈希值（防止重复）"""
        if not self.model_file:
            return ""
        # 重置文件指针到开头
        self.model_file.seek(0)
        hash_obj = hashlib.md5()
        # 分块读取文件，避免内存溢出
        for chunk in self.model_file.chunks(chunk_size=4096):
            hash_obj.update(chunk)
        # 恢复文件指针
        self.model_file.seek(0)
        return hash_obj.hexdigest()