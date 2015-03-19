# -*- coding: utf-8 -*-

from django.test import TestCase

from dbmail.models import MailTemplate


class TemplateTestCase(TestCase):

    def __create_template(self):
        return MailTemplate.objects.create(
            name="Site welcome template",
            subject="Welcome",
            message="Welcome to our site. We are glad to see you.",
            slug="welcome",
            is_html=False,
            id=1,
        )

    def __retrieve_named_template_and_check_num_queries(self, num):
        with self.assertNumQueries(num):
            template = MailTemplate.get_template("welcome")
            self.assertEqual(template.pk, 1)

    def test_retrieve_named_template(self):
        self.__create_template()
        self.__retrieve_named_template_and_check_num_queries(3)

    def test_retrieve_named_template_cached(self):
        self.test_retrieve_named_template()
        self.__retrieve_named_template_and_check_num_queries(0)

    def test_retrieve_named_template_with_cache_invalidation(self):
        self.test_retrieve_named_template_cached()

        template = MailTemplate.objects.get(pk=1)
        template.subject = "Hello"
        template.save()

        self.__retrieve_named_template_and_check_num_queries(3)

    def test_retrieve_named_template_with_cache_invalidation_cache(self):
        self.test_retrieve_named_template_with_cache_invalidation()
        self.__retrieve_named_template_and_check_num_queries(0)
