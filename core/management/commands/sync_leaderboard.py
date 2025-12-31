from django.core.management.base import BaseCommand
from core.models import UserProfile, Leaderboard

class Command(BaseCommand):
    help = 'Синхронизирует таблицу лидеров с профилями пользователей'

    def handle(self, *args, **options):
        profiles = UserProfile.objects.all()
        synced = 0
        created = 0
        
        for profile in profiles:
            leaderboard, was_created = Leaderboard.objects.get_or_create(
                user_profile=profile,
                defaults={'points': profile.xp}
            )
            
            if was_created:
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Создана запись для {profile.user.username}: {profile.xp} XP')
                )
            else:
                # Обновляем очки если они отличаются
                if leaderboard.points != profile.xp:
                    leaderboard.points = profile.xp
                    leaderboard.save()
                    synced += 1
                    self.stdout.write(
                        self.style.WARNING(f'Обновлена запись для {profile.user.username}: {profile.xp} XP')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nГотово! Создано: {created}, Обновлено: {synced}')
        )
