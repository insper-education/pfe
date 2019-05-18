from setuptools import setup

setup(
   name='pfe',
   version='0.1',
   description='Para controle dos projetos',
   author='Luciano Pereira Soares',
   author_email='lpsoares@insper.edu.br',
   packages=['pfe'],
   install_requires=['django', 'django-import-exportgreek'],
)