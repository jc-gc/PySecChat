from setuptools import setup

setup(name='PySecChat',
      version='0.1',
      description='Chat/Server application with encrypted messaging',
      url='https://github.com/wolfyxk/PySecChat',
      install_requires=[
          'tkintertable',
          'pygubu',
          'pycryptodomex',
      ],
      zip_safe=False)
