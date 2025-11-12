"""
Submissions app models - RDB redesign with soft delete.
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Submission(models.Model):
    """User submission model with soft delete."""
    
    class Status(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        PRIVATE = 'PRIVATE', 'Private'
        FLAGGED = 'FLAGGED', 'Flagged'
    
    # Author
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    
    # Content
    image = models.ImageField(upload_to='submissions/', blank=True, null=True)
    caption = models.TextField(max_length=1000, blank=True)
    comment_enabled = models.BooleanField(default=True)
    
    # Status and moderation
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PUBLIC)
    
    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    delete_reason = models.TextField(blank=True, null=True)
    
    # Legacy fields (for migration compatibility)
    aim = models.CharField(max_length=100, blank=True)
    steps = models.JSONField(default=list, blank=True)
    frame_type = models.CharField(max_length=50, blank=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    video_url = models.URLField(max_length=500, blank=True, null=True)
    game_url = models.URLField(max_length=500, blank=True, null=True)
    jp_result = models.CharField(max_length=10, default='none', blank=True)
    likes_count = models.IntegerField(default=0)
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'submissions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['deleted_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'Submission by {self.author.display_id} at {self.created_at}'
    
    def soft_delete(self, reason=None):
        """Soft delete the submission."""
        self.deleted_at = timezone.now()
        if reason:
            self.delete_reason = reason
        self.save()
    
    def restore(self):
        """Restore a soft-deleted submission."""
        self.deleted_at = None
        self.delete_reason = None
        self.save()


class Reaction(models.Model):
    """User reactions to submissions."""
    
    class Type(models.TextChoices):
        SUBMIT_MEDAL = 'submit_medal', 'Submit Medal'
    
    type = models.CharField(max_length=50, choices=Type.choices)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='reactions')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reactions'
        unique_together = [['user', 'submission', 'type']]
        indexes = [
            models.Index(fields=['submission', 'type']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.user.display_id} - {self.type} on {self.submission.id}'
