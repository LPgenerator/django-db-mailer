Usage
=====

To use django-db-mailer in a project::

    from dbmail.models import MailTemplate
    from dbmail import send_db_mail

    # New dbmail template
    MailTemplate.objects.create(
        name="Site welcome template",
        subject="Welcome",
        message="Welcome to our site. We are glad to see you.",
        slug="welcome",
        is_html=False,
    )

    # Send message with created template
    send_db_mail(
        # slug was defined on db template
        slug='welcome',

        # recipient can be list, or separated with comma or simple string
        # 'user1@example.com' or 'user1@example.com, user2@example.com' or ['user1@example.com', 'user2@example.com']
        recipient='user1@example.com',

        # All *args params will be accessible on template context
        {
            'username': request.user.username,
            'full_name': request.user.get_full_name(),
            'signup_date': request.user.date_joined
        },

        # You can access to all model fields. For m2m and fk fields, you should use module_name
        MyModel.objects.get(pk=1),

        # Optional kwargs:
        # from_email='from@example.com'
        # cc=['cc@example.com'],
        # bcc=['bcc@example.com'],
        # user=User.objects.get(pk=1),
        # from_email='bcc@example.com',
        # attachments=[(filename, content, mimetype)],
        # headers={'Custom-Header':'Some value'},
    )
