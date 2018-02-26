from  setuptools import setup, find_packages

install_requires = ['requests']

setup(
    name='coinex',
    packages=find_packages(),
    author_email = 'chiangqiqi@gmail.com',
    author='Alex Jiang',
    version='0.0.1',
    url = 'https://github.com/chiangqiqi/pyhuobi',
    description='coinex simple restful api',
    install_requires=install_requires
)
