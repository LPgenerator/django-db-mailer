# Импорт CSV в MailGroup

`MailGroup` — встроенная модель управления списком: именованный
slug, который резолвится в список получателей (`MailGroupEmail`).
Когда в группе есть участники, `send_db_mail("welcome", "your-group-slug", ...)`
делает fan-out по всем.

В 3.0 встроенного admin-импорта CSV нет (запланирован на 3.1). Пока
используйте management shell или одноразовый скрипт.

## Формат

```csv
name,email
Алиса,alice@example.com
Боб,bob@example.com
Кэрол,carol@example.com
```

Колонка `email` обязательна; остальное опционально. Для SMS / push
колонка по историческим причинам тоже называется `email` —
`MailGroupEmail.email` это `CharField`, не валидируется как email,
поэтому туда же кладите телефоны / device tokens.

## Через shell (одноразово)

```python
import csv
from dbmail.models import MailGroup, MailGroupEmail

group, _ = MailGroup.objects.get_or_create(
    name="Подписчики",
    slug="subscribers",
)

with open("/path/to/contacts.csv", encoding="utf-8") as fh:
    reader = csv.DictReader(fh)
    rows = [
        MailGroupEmail(
            group=group,
            name=r.get("name") or r["email"],
            email=r["email"].strip(),
        )
        for r in reader
        if r.get("email")
    ]

# bulk_create — без лишних запросов
MailGroupEmail.objects.bulk_create(rows, ignore_conflicts=True, batch_size=500)
print(f"Импортировано {len(rows)} адресов в группу '{group.slug}'")
```

## Re-runnable management command

```python
# myapp/management/commands/import_subscribers.py
from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from dbmail.models import MailGroup, MailGroupEmail


class Command(BaseCommand):
    help = "Импорт CSV (name,email) в MailGroup."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Путь к CSV")
        parser.add_argument("--slug", required=True, help="Slug целевой MailGroup")
        parser.add_argument("--name", default=None, help="MailGroup.name (auto-create)")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        path = Path(opts["path"])
        if not path.exists():
            raise CommandError(f"{path} не найден")

        group, created = MailGroup.objects.get_or_create(
            slug=opts["slug"],
            defaults={"name": opts["name"] or opts["slug"]},
        )
        if created:
            self.stdout.write(self.style.NOTICE(f"создана MailGroup {group.slug!r}"))

        with path.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = [
                MailGroupEmail(
                    group=group,
                    name=(r.get("name") or r["email"]).strip(),
                    email=r["email"].strip(),
                )
                for r in reader
                if (r.get("email") or "").strip()
            ]

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING(f"DRY-RUN — будет импортировано {len(rows)} строк"))
            return

        MailGroupEmail.objects.bulk_create(rows, ignore_conflicts=True, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Импортировано {len(rows)} адресов в {group.slug!r}"))
```

```bash
python manage.py import_subscribers contacts.csv --slug subscribers --name "Подписчики"
```

`ignore_conflicts=True` пропускает дубликаты без exception — можно
безопасно повторно запускать на том же файле. Добавьте флаг
`--prune`, если нужно удалять адреса, исчезнувшие из источника.

## Отправка по импортированной группе

```python
from dbmail import send_db_mail

# Получатель распознан как MailGroup.slug — нет @ или +
send_db_mail("welcome", "subscribers", {"campaign": "Сентябрь"})
```

Для огромных групп (>10k участников) предпочтите Celery — `Sender`
по умолчанию шлёт последовательно по получателям (batch-оптимизация
PERF-1 запланирована на 3.0.1).

## Кеш

`MailGroup.get_emails(slug)` материализует список адресов и кеширует
под slug. После импорта вызовите:

```python
from dbmail.models import MailGroup
MailGroup(slug="subscribers").clean_cache()
```

…или дождитесь `MailGroup.save()` (post-import script родительскую
группу не меняет).
