from django.core.management.base import BaseCommand, CommandError
from apps.users.models import User


class Command(BaseCommand):
    help = 'Assign a role to a user by username'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username')
        parser.add_argument('role', type=str, help='Role to assign', 
                          choices=[choice[0] for choice in User.Role.choices])

    def handle(self, *args, **options):
        username = options['username']
        role = options['role']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User with username "{username}" does not exist')

        user.set_role(role)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set role "{user.get_role_display()}" for user "{username}"'
            )
        )
        
        # Display current role
        self.stdout.write(f'Current role: {user.get_role_display()}')
