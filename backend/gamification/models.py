"""
Gamification app models.
"""
from django.db import models


class Title(models.Model):
    """Title master data."""
    name = models.CharField('称号名', max_length=100, unique=True)
    color = models.CharField('色', max_length=50, blank=True, null=True)
    duration_days = models.IntegerField('有効期間（日）', default=7)
    image = models.ImageField('バナー画像', upload_to='titles/', blank=True, null=True, help_text='称号のバナー画像（321×115px推奨）をアップロードします。')
    image_url = models.URLField('画像URL', max_length=500, blank=True, null=True, help_text='外部URLから画像を指定する場合に使用します。')
    
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        db_table = 'titles'
        verbose_name = '称号'
        verbose_name_plural = '称号'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Card(models.Model):
    """Card master data."""
    
    class Rarity(models.TextChoices):
        COMMON = 'common', 'コモン'
        RARE = 'rare', 'レア'
        SEASONAL = 'seasonal', 'シーズナル'
        SPECIAL = 'special', 'スペシャル'
    
    class CardType(models.TextChoices):
        CHARACTER = 'character', 'キャラクターカード'
        EFFECT = 'effect', 'エフェクトカード'
    
    code = models.CharField('コード', max_length=50, unique=True, db_index=True)
    name = models.CharField('カード名', max_length=100)
    rarity = models.CharField('レアリティ', max_length=20, choices=Rarity.choices, default=Rarity.COMMON)
    image = models.ImageField('画像', upload_to='cards/', blank=True, null=True, help_text='カードの画像をアップロードします。')
    image_url = models.URLField('画像URL', max_length=500, blank=True, null=True, help_text='外部URLから画像を指定する場合に使用します。')
    description = models.TextField('カード説明', blank=True, null=True)
    # 追加項目
    attribute = models.CharField('属性', max_length=50, blank=True, null=True)
    atk_points = models.IntegerField('ATKポイント', blank=True, null=True)
    def_points = models.IntegerField('DEFポイント', blank=True, null=True)
    card_type = models.CharField(
        'カード種別',
        max_length=20,
        choices=CardType.choices,
        blank=True,
        null=True,
        help_text='キャラクターカードかエフェクトカードか',
    )
    buff_effect = models.TextField('バフ効果', blank=True, null=True)
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cards'
        verbose_name = 'カード'
        verbose_name_plural = 'カード'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['rarity']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'{self.code} - {self.name}'

