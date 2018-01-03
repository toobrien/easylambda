
from distutils.core import setup

setup(
  name="easylambda",
  version="1.0",
  url='https://www.github.com/toobrien/easylambda',
  packages=['src/easylambda'],
  package_data={
    'easylambda': [
        'src/resources/pom_template',
        'src/resources/handler_template'
      ]
  }
)
