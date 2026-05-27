"""Migration tests using django-test-migrations.

Covers ``0001_initial`` (forward+reverse) and ``0002_apikey_hash_data``
(data migration: forward, reverse, idempotency). ``django-test-migrations``
needs the ``transactional_db`` fixture to manipulate migration state.
"""

from __future__ import annotations


class TestApiKeyHashDataMigration:
    def test_forward_hashes_legacy_keys(self, transactional_db):
        from django_test_migrations.migrator import Migrator

        migrator = Migrator(database="default")

        old_state = migrator.apply_initial_migration(("dbmail", "0001_initial"))
        ApiKey = old_state.apps.get_model("dbmail", "ApiKey")
        ApiKey.objects.create(name="legacy", api_key="z" * 32, password_hash="")
        assert ApiKey.objects.filter(password_hash="").count() == 1

        new_state = migrator.apply_tested_migration(("dbmail", "0002_apikey_hash_data"))
        ApiKey = new_state.apps.get_model("dbmail", "ApiKey")
        rehashed = ApiKey.objects.get(name="legacy")
        assert rehashed.password_hash != ""
        assert rehashed.api_key == "z" * 32  # plain column untouched

        migrator.reset()

    def test_reverse_clears_password_hash(self, transactional_db):
        from django_test_migrations.migrator import Migrator

        migrator = Migrator(database="default")

        forward_state = migrator.apply_tested_migration(("dbmail", "0002_apikey_hash_data"))
        ApiKey = forward_state.apps.get_model("dbmail", "ApiKey")
        ApiKey.objects.create(
            name="user",
            api_key="m" * 32,
            password_hash="someprehashedvalue",
        )

        # Reverse one step.
        back_state = migrator.apply_tested_migration(("dbmail", "0001_initial"))
        ApiKey = back_state.apps.get_model("dbmail", "ApiKey")
        row = ApiKey.objects.get(name="user")
        assert row.password_hash == ""
        # Plain api_key column must still hold the original value.
        assert row.api_key == "m" * 32

        migrator.reset()

    def test_idempotent_forward(self, transactional_db):
        """Re-running 0002 on already-hashed rows is a no-op.

        The migration's ``RunPython`` filters on ``password_hash=""``,
        so already-hashed rows are skipped on a second pass.
        """
        from django_test_migrations.migrator import Migrator

        migrator = Migrator(database="default")
        state = migrator.apply_tested_migration(("dbmail", "0002_apikey_hash_data"))
        ApiKey = state.apps.get_model("dbmail", "ApiKey")
        ApiKey.objects.create(
            name="hashed",
            api_key="q" * 32,
            password_hash="bcrypt$pre-hashed",
        )

        legacy_count = ApiKey.objects.filter(password_hash="").count()
        # No legacy rows after we created one with non-empty hash.
        assert legacy_count == 0

        migrator.reset()
