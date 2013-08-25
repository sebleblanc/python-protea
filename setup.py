import os

from distutils.core import setup

def read(file):
    return open( os.path.join(os.path.dirname(__file__), file) ).read()

setup(name='Protea',
      version='0.1a',
      description='Ashly digital audio products RS-232 interface library',
      author='Sébastien Leblanc',
      author_email='seb@sebleblanc.net',
      url='https://github.com/sebleblanc/python-protea/',
      license='MIT',
      keywords='ashly protea ne24.24M 4.24C matrix processor interface rs-232',

      long_description=read('README.md'),
      packages=['protea'],
      classifiers=[
          "Development Status :: 3 - Alpha",

          "Intended Audience :: Developers",
          "Intended Audience :: System Administrators",
          "Intended Audience :: Telecommunications Industry",

          "Topic :: Multimedia :: Sound/Audio",
          "Topic :: Terminals :: Serial",
          "Topic :: System :: Hardware :: Hardware Drivers",
          "Topic :: Utilities",


          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 3",

          "License :: OSI Approved :: MIT License",
          
          "Operating System :: POSIX :: Linux"
          "Operating System :: Microsoft :: Windows",
      ]
)
