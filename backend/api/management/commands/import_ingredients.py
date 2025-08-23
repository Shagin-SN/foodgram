import os
import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из data/ingredients.csv'

    def print_progress(self, current, total, created, duplicates, errors):
        progress = (current / total) * 100 if total > 0 else 0
        self.stdout.write(
            f'\rПрогресс: {progress:.1f}% | '
            f'Создано: {created} | '
            f'Дубликаты: {duplicates} | '
            f'Ошибки: {errors} | '
            f'Обработано: {current}/{total}',
            ending=''
        )

    def handle(self, *args, **options):
        csv_file_path = os.path.join(
            settings.BASE_DIR, 'data', 'ingredients.csv')

        self.stdout.write(
            self.style.SUCCESS(f'Путь к файлу: {csv_file_path}')
        )
        if not os.path.exists(csv_file_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {csv_file_path} не найден!')
            )
            self.stdout.write(
                self.style.WARNING(
                    'Создайте файл ingredients.csv в папке data/')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('Начинаю импорт ингредиентов...')
        )

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                total_lines = sum(1 for line in file)

            if total_lines == 0:
                self.stdout.write(
                    self.style.WARNING('Файл пустой')
                )
                return

            ingredients_to_create = []
            duplicates = 0
            created = 0
            errors = 0
            processed = 0

            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)

                for row_num, row in enumerate(reader, 1):
                    processed += 1

                    if len(row) < 2:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Строка {row_num}: '
                                f'недостаточно данных - {row}')
                        )
                        errors += 1
                        continue

                    name = row[0].strip()
                    measurement_unit = row[1].strip()

                    if not name:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Строка {row_num}: пустое '
                                f'название ингредиента')
                        )
                        errors += 1
                        continue

                    if not measurement_unit:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Строка {row_num}: пустая единица '
                                f'измерения для "{name}"')
                        )
                        errors += 1
                        continue

                    if Ingredient.objects.filter(
                        name__iexact=name,
                        measurement_unit__iexact=measurement_unit
                    ).exists():
                        duplicates += 1
                    else:
                        ingredients_to_create.append(
                            Ingredient(
                                name=name,
                                measurement_unit=measurement_unit
                            )
                        )
                        created += 1

                    if processed % 50 == 0 or processed == total_lines:
                        self.print_progress(
                            processed,
                            total_lines,
                            created,
                            duplicates,
                            errors)

            if ingredients_to_create:
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write('Создаю ингредиенты в базе данных...')

                Ingredient.objects.bulk_create(
                    ingredients_to_create,
                    batch_size=500,
                    ignore_conflicts=True
                )

            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(
                self.style.SUCCESS(
                    'ИМПОРТ ЗАВЕРШЕН!\n'
                    f'Всего строк в файле: {total_lines}\n'
                    f'Обработано данных: {processed}\n'
                    f'Успешно создано: {created}\n'
                    f'Пропущено дубликатов: {duplicates}\n'
                    f'Ошибок формата: {errors}\n'
                    f'Общее количество ингредиентов в базе: '
                    f'{Ingredient.objects.count()}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при импорте: {str(e)}')
            )
