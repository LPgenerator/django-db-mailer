from setuptools import setup, find_packages
from dbmail import get_version


setup(
    name='django-db-mailer',
    version=get_version(),
    description='Django module to easily send emails using '
                'django templates stored on database.',
    keywords="django db mail email html text tts sms push templates mailer",
    long_description=open('README.rst').read(),
    author="GoTLiuM InSPiRiT",
    author_email='gotlium@gmail.com',
    url='http://github.com/LPgenerator/django-db-mailer/',
    packages=find_packages(exclude=['demo']),
    package_data={'dbmail': [
        'locale/*/LC_MESSAGES/django.*',
        'static/dbmail/admin/js/*.js',
        'fixtures/*.json',
    ]},
    include_package_data=True,
    install_requires=[
        'setuptools',
    ],
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
