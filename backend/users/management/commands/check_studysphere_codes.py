"""
Django management command to check StudySphere login codes in the database.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Check StudySphere login codes in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Check specific user ID',
        )
        parser.add_argument(
            '--display-id',
            type=str,
            help='Check specific user by display_id',
        )
        parser.add_argument(
            '--token',
            type=str,
            help='Search for a specific token',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        display_id = options.get('display_id')
        token = options.get('token')

        if user_id:
            users = User.objects.filter(id=user_id)
        elif display_id:
            users = User.objects.filter(display_id=display_id)
        elif token:
            users = User.objects.filter(studysphere_login_code=token)
            if not users.exists():
                # 大文字小文字を無視して検索
                users = User.objects.filter(studysphere_login_code__iexact=token)
        else:
            # すべてのユーザーでstudysphere_login_codeが設定されているものを表示
            users = User.objects.exclude(studysphere_login_code__isnull=True).exclude(studysphere_login_code='')

        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found matching the criteria.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {users.count()} user(s):\n'))

        for user in users:
            login_code = user.studysphere_login_code or '(not set)'
            user_id_val = user.studysphere_user_id or '(not set)'
            
            self.stdout.write(f'User ID: {user.id}')
            self.stdout.write(f'  Display ID: {user.display_id}')
            self.stdout.write(f'  Email: {user.email or "(not set)"}')
            self.stdout.write(f'  StudySphere User ID: {user_id_val}')
            self.stdout.write(f'  StudySphere Login Code: {login_code}')
            self.stdout.write(f'  Login Code Length: {len(login_code) if login_code != "(not set)" else 0}')
            if login_code != '(not set)':
                self.stdout.write(f'  Login Code Preview: {login_code[:20]}...' if len(login_code) > 20 else f'  Login Code Preview: {login_code}')
            self.stdout.write('')
