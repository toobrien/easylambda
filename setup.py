
from distutils.core import setup

setup(
  name="easylambda",
  version="1.0",
  url='https://www.github.com/toobrien/easylambda',
  packages=['easylambda'],
  package_data={
    'easylambda': [
        'resources/pom_template',
        'resources/handler_template'
      ]
  }
)
