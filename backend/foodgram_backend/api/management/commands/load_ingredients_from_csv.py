import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load data from ingredients.csv into the database'

    def handle(self, *args, **options):
        csv_file_path = 'ingredients.csv'

        with open(csv_file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file, ['name', 'measurement_unit'])

            for row in csv_reader:
                name = Ingredient(name=row['name'],
                                  measurement_unit=row['measurement_unit'])
                name.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded data from {csv_file_path}')
                )
