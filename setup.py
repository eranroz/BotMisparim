from distutils.core import setup

setup(
    name='botMisparim',
    version='1.0',
    packages=[''],
    scripts=['misparim.py'],
    url='https://github.com/eranroz/BotMisparim',
    license='MIT',
    author='eranroz',
    author_email='eranroz@cs.huji.ac.il',
    description='Bot for scanning common grammar mistakes in Hebrew',
    requires=['HspellPy', 'pywikibot']
)
