from setuptools import setup

setup(name='meetdoelenproject',
      version='0.3',
      description='Meetdoelenproject ter optimalisatie van Vitens-meetnet',
      url='https://github.com/mgjmulder/Vitens-Meetdoelenproject/',
      author='Martijn Mulder',
      author_email='martijn.mulder@vitens.nl',
      packages=['meetdoelenproject'],
      zip_safe=False,
      install_requires=['collections',
                        'gdal',
                        'gdalnumeric',
                        'geopandas',
                        'imod',
                        'numpy',
                        'pandas',
                        'shapely'])