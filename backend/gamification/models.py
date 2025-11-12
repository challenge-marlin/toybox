"""
Gamification app models.
"""
from django.db import models


class Title(models.Model):
    """Title master data."""
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    duration_days = models.IntegerField(default=7)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'titles'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Card(models.Model):
    """Card master data."""
    
    class Rarity(models.TextChoices):
        COMMON = 'common', 'Common'
        RARE = 'rare', 'Rare'
        SEASONAL = 'seasonal', 'Seasonal'
        SPECIAL = 'special', 'Special'
    
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    rarity = models.CharField(max_length=20, choices=Rarity.choices, default=Rarity.COMMON)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cards'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['rarity']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'{self.code} - {self.name}'

