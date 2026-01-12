from django.core.management.base import BaseCommand
from django.db import transaction
from apps.notifications.models.gradus_models import Channel, Variable, NotificationType


class Command(BaseCommand):
    help = 'Seed initial data for notifications: channels, variables, and notification types'

    def handle(self, *args, **options):
        self.stdout.write('Starting seed process...')
        
        try:
            with transaction.atomic():
                # 1. Create Channels
                self.stdout.write('Creating channels...')
                channels_data = [
                    {'title': 'email', 'allowed_tags': ['p', 'b', 'i', 'a', 'br']},
                    {'title': 'telegram', 'allowed_tags': ['p', 'br']},
                    {'title': 'viber', 'allowed_tags': ['p', 'br']},
                    {'title': 'push', 'allowed_tags': []},
                ]
                
                channels = {}
                for ch_data in channels_data:
                    channel, created = Channel.objects.get_or_create(
                        title=ch_data['title'],
                        defaults={'allowed_tags': ch_data['allowed_tags']}
                    )
                    if not created:
                        channel.allowed_tags = ch_data['allowed_tags']
                        channel.save()
                    channels[ch_data['title']] = channel
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Channel: {channel.title}'))
                
                # 2. Create Variables
                self.stdout.write('Creating variables...')
                variables_data = [
                    'title',
                    'confirmation_token',
                    'username',
                ]
                
                variables = {}
                for var_name in variables_data:
                    variable, created = Variable.objects.get_or_create(title=var_name)
                    variables[var_name] = variable
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Variable: {variable.title}'))
                
                # 3. Create Notification Types
                self.stdout.write('Creating notification types...')
                
                # new survey
                new_survey, created = NotificationType.objects.get_or_create(
                    title='new survey',
                    defaults={'is_custom': False}
                )
                if not created:
                    new_survey.is_custom = False
                    new_survey.save()
                new_survey.channels.set([
                    channels['email'],
                    channels['telegram'],
                    channels['viber'],
                    channels['push']
                ])
                new_survey.variables.set([variables['title']])
                if not new_survey.channels.exists():
                    raise ValueError(f'NotificationType "{new_survey.title}" must have at least one channel')
                self.stdout.write(self.style.SUCCESS(f'  ✓ NotificationType: {new_survey.title}'))
                
                # confirm email
                confirm_email, created = NotificationType.objects.get_or_create(
                    title='confirm email',
                    defaults={'is_custom': False}
                )
                if not created:
                    confirm_email.is_custom = False
                    confirm_email.save()
                confirm_email.channels.set([channels['email']])
                confirm_email.variables.set([variables['confirmation_token']])
                if not confirm_email.channels.exists():
                    raise ValueError(f'NotificationType "{confirm_email.title}" must have at least one channel')
                self.stdout.write(self.style.SUCCESS(f'  ✓ NotificationType: {confirm_email.title}'))
                
                # bot successful subscribe
                bot_subscribe, created = NotificationType.objects.get_or_create(
                    title='bot successful subscribe',
                    defaults={'is_custom': False}
                )
                if not created:
                    bot_subscribe.is_custom = False
                    bot_subscribe.save()
                bot_subscribe.channels.set([
                    channels['telegram'],
                    channels['viber']
                ])
                bot_subscribe.variables.set([variables['username']])
                if not bot_subscribe.channels.exists():
                    raise ValueError(f'NotificationType "{bot_subscribe.title}" must have at least one channel')
                self.stdout.write(self.style.SUCCESS(f'  ✓ NotificationType: {bot_subscribe.title}'))
                
                # custom
                custom_type, created = NotificationType.objects.get_or_create(
                    title='custom',
                    defaults={'is_custom': True}
                )
                if not created:
                    custom_type.is_custom = True
                    custom_type.save()
                custom_type.channels.set([
                    channels['email'],
                    channels['telegram'],
                    channels['viber'],
                    channels['push']
                ])
                custom_type.variables.clear()  # custom types have no variables
                if not custom_type.channels.exists():
                    raise ValueError(f'NotificationType "{custom_type.title}" must have at least one channel')
                self.stdout.write(self.style.SUCCESS(f'  ✓ NotificationType: {custom_type.title}'))
            
            self.stdout.write(self.style.SUCCESS('\n✓ Seed process completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error during seed process: {str(e)}'))
            raise
