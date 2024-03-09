from setuptools import setup, find_packages

setup(
    name='assignment1',
    version='1.0',
    author='Pratiksha Deodhar',
    author_email='pratikshadeo24@gmail.com',
    url="https://github.com/pratikshadeo24/cis6930sp24-assignment1",
    packages=find_packages(exclude=('tests', 'docs')),
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)
