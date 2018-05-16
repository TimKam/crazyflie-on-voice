import codecs, setuptools

setuptools.setup(
    name='crazyflie-on-voice',
    packages=['src'],
    version='0.0.1',
    description='Voice control Crazyflie 2.0s',
    author='Christopher Blöcker, Timotheus Kampik, Tobias Sundqvist',
    author_email='christopher.blocker@umu.se, tkampik@cs.umu.se, sundqtob@cs.umu.se',
    url='https://github.com/TimKam/crazyflie-on-voice',
    platforms=["any"],
    license="MIT",
    zip_safe=False,
    install_requires=[],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Documentation",
    ],
    long_description=codecs.open("README.rst", "r", "utf-8").read(),
)
