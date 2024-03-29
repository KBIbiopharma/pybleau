from glob import glob
from os.path import abspath, dirname, join

from setuptools import setup, find_packages

HERE = dirname(abspath(__file__))

PKG_NAME = "pybleau"

info = {}
init_file = join(HERE, PKG_NAME, "__init__.py")
exec(open(init_file).read(), globals(), info)


def read(fname):
    """ Returns content of the passed file. """
    return open(join(HERE, fname)).read()


# Application image files -----------------------------------------------------
ui_app_images_files = glob(join(PKG_NAME, "app", "images", "*.png"))


setup(
    name=PKG_NAME,
    version=info["__version__"],
    author='KBI Biopharma Inc.',
    author_email='jrocher@kbibiopharma.com',
    license='MIT',
    url='http://www.kbibiopharma.com/',
    description='plotly Dash and ETS-based dataframe exploration tools',
    long_description=read('README.md'),
    ext_modules=[],
    packages=find_packages(),
    install_requires=[],
    requires=[],
    # Additional data files
    data_files=[
        (join(PKG_NAME, "app", "images"), ui_app_images_files),
    ],
    package_data={
        "": ["README.md", "LICENSE"],
        PKG_NAME: ["reporting/tests/*.png",
                   "reporting/tests/*.json",
                   "images/*.png"]
    },
    entry_points={
        'console_scripts': [
            'pybleau_app = {}.app.main:main'.format(PKG_NAME),
            'pybleau_report={}.reporting.app.main:main'.format(PKG_NAME),
        ],
      },
)
