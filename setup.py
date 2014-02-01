from setuptools import setup, find_packages

version = '0.1'

setup(name='ppm',
      version=version,
      url = 'https://github.com/predictix/ppm',
      description="project package manager, a tool for managing general project dependencies",
      long_description="",
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
      ],
      keywords='package manager',
      author='Amine Hajyoussef',
      author_email='hajyoussef.amine@gmail.com',
      license='MIT',
      packages=find_packages(exclude=['registry', 'tests', 'mirror']),
      entry_points={
        'console_scripts': [
            'ppm=ppm.main:parseArguments',
        ],
      },
)
