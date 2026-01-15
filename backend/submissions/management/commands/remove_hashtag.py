"""
Django management command to remove a specific hashtag from all submissions.
"""
from django.core.management.base import BaseCommand
from submissions.models import Submission


class Command(BaseCommand):
    help = 'Remove a specific hashtag from all submissions'

    def add_arguments(self, parser):
        parser.add_argument(
            'hashtag',
            type=str,
            help='Hashtag to remove (case-insensitive)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run mode (show what would be removed without actually removing)'
        )

    def handle(self, *args, **options):
        hashtag_to_remove = options['hashtag'].strip().lower()
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get all submissions with hashtags
        submissions = Submission.objects.filter(
            deleted_at__isnull=True
        ).exclude(hashtags__isnull=True).exclude(hashtags=[])

        updated_count = 0
        total_removed = 0

        for submission in submissions:
            if not submission.hashtags or not isinstance(submission.hashtags, list):
                continue

            # Check if the hashtag exists (case-insensitive)
            original_hashtags = submission.hashtags.copy()
            updated_hashtags = [
                tag for tag in submission.hashtags
                if tag and isinstance(tag, str) and tag.strip().lower() != hashtag_to_remove
            ]

            # If hashtags were removed, update the submission
            if len(updated_hashtags) != len(original_hashtags):
                removed_count = len(original_hashtags) - len(updated_hashtags)
                total_removed += removed_count

                if not dry_run:
                    submission.hashtags = updated_hashtags
                    submission.save(update_fields=['hashtags'])

                updated_count += 1
                self.stdout.write(
                    f"{'Would remove' if dry_run else 'Removed'} {removed_count} instance(s) "
                    f"of '{hashtag_to_remove}' from submission {submission.id} "
                    f"(author: {submission.author.display_id})"
                )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nDRY RUN: Would update {updated_count} submission(s) '
                    f'and remove {total_removed} instance(s) of "{hashtag_to_remove}"'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully updated {updated_count} submission(s) '
                    f'and removed {total_removed} instance(s) of "{hashtag_to_remove}"'
                )
            )
