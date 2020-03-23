from setuptools import setup

setup(name='meetdoelenproject',
      version='0.1',
      description='Meetdoelenproject ter optimalisatie van Vitens-meetnet',
      url='https://github.com/mgjmulder/Vitens-Meetdoelenproject',
      author='Martijn Mulder',
      author_email='martijn.mulder@vitens.nl',
      packages=['pyhydro'],
      install_requires=['collections',
			'gdal',
			'gdalnumeric',
			'geopandas',
			'imod',
                        'numpy',
			'os',
                        'pandas',
                        'shapely'],
       zip_safe=False)