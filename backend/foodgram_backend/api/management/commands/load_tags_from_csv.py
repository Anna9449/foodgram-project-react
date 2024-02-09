import csv

from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Load data from tags.csv into the database'

    def handle(self, *args, **options):
        csv_file_path = 'tags.csv'

        try:
            with open(csv_file_path, 'r', encoding='UTF-8') as csv_file:
                csv_reader = csv.DictReader(csv_file, ['name', 'slug',
                                                       'color'])
                for row in csv_reader:
                    name = Tag(name=row['name'],
                               slug=row['slug'],
                               color=row['color'])
                    name.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully loaded data from {csv_file_path}')
                    )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    f'File {csv_file_path} - not found')
            )
