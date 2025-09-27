from django.core.management.base import BaseCommand
from files.models import Language, MediaLanguage

class Command(BaseCommand):
    help = 'Load APAC languages safely without conflicts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing entries if they exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created/updated without making changes',
        )

    def handle(self, *args, **options):
        languages_data = [
            {"code": "ar", "title": "Arabic"},
            {"code": "ba", "title": "Bangla"},
            {"code": "be", "title": "Bengali"},
            {"code": "my", "title": "Burmese"},
            {"code": "km", "title": "Cambodian"},
            {"code": "ca", "title": "Cantonese"},
            {"code": "ce", "title": "Cebuano"},
            {"code": "ch", "title": "Chammoro"},
            {"code": "dh", "title": "Dhivehi"},
            {"code": "dz", "title": "Dzongkha"},
            {"code": "en", "title": "English"},
            {"code": "fi", "title": "Fijian"},
            {"code": "fr", "title": "French"},
            {"code": "de", "title": "German"},
            {"code": "ha", "title": "Halia"},
            {"code": "hi", "title": "Hindi"},
            {"code": "ind", "title": "Indonesian"},
            {"code": "it", "title": "Italian"},
            {"code": "ja", "title": "Japanese"},
            {"code": "jw", "title": "Javanese"},
            {"code": "ka", "title": "Karen"},
            {"code": "kh", "title": "Khmer"},
            {"code": "ko", "title": "Korean"},
            {"code": "la", "title": "Lao"},
            {"code": "ma", "title": "Madurese"},
            {"code": "mg", "title": "Malagasy"},
            {"code": "ms", "title": "Malay"},
            {"code": "man", "title": "Mandarin"},
            {"code": "mi", "title": "Maori"},
            {"code": "mo", "title": "Mongolian"},
            {"code": "ne", "title": "Nepali"},
            {"code": "pal", "title": "Palauan"},
            {"code": "pas", "title": "Pashtu"},
            {"code": "pi", "title": "Pitkern"},
            {"code": "pt", "title": "Portugese"},
            {"code": "pa", "title": "Punjabi"},
            {"code": "ru", "title": "Russian"},
            {"code": "sm", "title": "Samoan"},
            {"code": "si", "title": "Sinhala"},
            {"code": "es", "title": "Spanish"},
            {"code": "su", "title": "Sundanese"},
            {"code": "tl", "title": "Tagalog"},
            {"code": "tai", "title": "Taiwanese"},
            {"code": "ta", "title": "Tamil"},
            {"code": "te", "title": "Tetum"},
            {"code": "th", "title": "Thai"},
            {"code": "bo", "title": "Tibetan"},
            {"code": "tok", "title": "Tokelauan"},
            {"code": "to", "title": "Tongan"},
            {"code": "ur", "title": "Urdu"},
            {"code": "vi", "title": "Vietnamese"},
            {"code": "automatic", "title": "Automatic Detection"},
            {"code": "automatic-translation", "title": "Auto-detect & Translate to English"},
        ]

        # Exclude automatic entries for MediaLanguage
        exclude_from_media_language = ["automatic", "automatic-translation"]

        created_languages = 0
        updated_languages = 0
        created_media_languages = 0
        updated_media_languages = 0

        for lang_data in languages_data:
            # Handle Language model
            if options['dry_run']:
                exists = Language.objects.filter(code=lang_data['code']).exists()
                if exists:
                    action = "update" if options.get("update") else "skip"
                    self.stdout.write(f"Would {action} Language: {lang_data['title']}")
                else:
                    self.stdout.write(f"Would create Language: {lang_data['title']}")
            else:
                language, created = Language.objects.get_or_create(
                    code=lang_data['code'],
                    defaults={'title': lang_data['title']}
                )

                if created:
                    created_languages += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created Language: {lang_data["title"]}')
                    )
                elif options['update']:
                    language.title = lang_data['title']
                    language.save()
                    updated_languages += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated Language: {lang_data["title"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(f'Skipped existing Language: {lang_data["title"]}')
                    )

            # Handle MediaLanguage model (exclude automatic entries)
            if lang_data['code'] not in exclude_from_media_language:
                if options['dry_run']:
                    exists = MediaLanguage.objects.filter(title=lang_data['title']).exists()
                    if exists:
                        self.stdout.write(f"Would update MediaLanguage: {lang_data['title']}")
                    else:
                        self.stdout.write(f"Would create MediaLanguage: {lang_data['title']}")
                else:
                    # Using actual MediaLanguage model fields
                    media_language, created = MediaLanguage.objects.get_or_create(
                        title=lang_data['title'],
                        defaults={
                            'media_count': 0,
                            'listings_thumbnail': '',  # Empty string, not null
                        }
                    )
                    if created:
                        created_media_languages += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created MediaLanguage: {lang_data["title"]}')
                        )
                    elif options['update']:
                        # Nothing to update for MediaLanguage currently; skipping.
                        self.stdout.write(self.style.WARNING(
                            f'No updatable fields for MediaLanguage: {lang_data["title"]}; skipped.'
                        ))
                    else:
                        self.stdout.write(
                            self.style.NOTICE(f'Skipped existing MediaLanguage: {lang_data["title"]}')
                        )

        if not options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSummary:\n'
                    f'Languages - Created: {created_languages}, Updated: {updated_languages}\n'
                    f'MediaLanguages - Created: {created_media_languages}, Updated: {updated_media_languages}'
                )
            )
        else:
            self.stdout.write(self.style.NOTICE('Dry run completed - no changes made'))