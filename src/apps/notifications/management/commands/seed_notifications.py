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
                new_survey = NotificationType.objects.filter(title='new survey').first()
                if not new_survey:
                    new_survey = NotificationType(title='new survey', is_custom=False)
                    new_survey.save()  # Save first to get pk
                else:
                    new_survey.is_custom = False
                    new_survey.save()
                new_survey.channels.set([
                    channels['email'],
                    channels['telegram'],
                    channels['viber'],
                    channels['push']
                ])
                new_survey.variables.set([variables['title']])
                # Validate channels after setting (object already has pk)
                if not new_survey.channels.exists():
                    raise ValueError(f'NotificationType "{new_survey.title}" must have at least one channel')
                self.stdout.write(self.style.SUCCESS(f'  ✓ NotificationType: {new_survey.title}'))
                
                # confirm email
                confirm_email = NotificationType.objects.filter(title='confirm email').first()
                if not confirm_email:
                    confirm_email = NotificationType(title='confirm email', is_custom=False)
                    confirm_email.save()  # Save first to get pk
                else:
                    confirm_email.is_custom = False
                    confirm_email.save()
                confirm_email.channels.set([channels['email']])
                confirm_email.variables.set([variables['confirmation_token']])
                if not confirm_email.channels.exists():
                    raise ValueError(f'NotificationType "{confirm_email.title}" must have at least one channel')
                self.stdout.write(self.style.SUCCESS(f'  ✓ NotificationType: {confirm_email.title}'))
                
                # bot successful subscribe
                bot_subscribe = NotificationType.objects.filter(title='bot successful subscribe').first()
                if not bot_subscribe:
                    bot_subscribe = NotificationType(title='bot successful subscribe', is_custom=False)
                    bot_subscribe.save()  # Save first to get pk
                else:
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
                custom_type = NotificationType.objects.filter(title='custom').first()
                if not custom_type:
                    custom_type = NotificationType(title='custom', is_custom=True)
                    custom_type.save()  # Save first to get pk
                else:
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
