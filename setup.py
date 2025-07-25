from setuptools import setup, find_packages

setup(
    name="bt_tracker_utils",
    version="0.1.1",
    author="JackyHe398",
    author_email="hekinghung@gmail.com",
    description="BitTorrent tracker utilities for checking availability and querying",
    install_requires=[
        "requests>=2.32.4",
        "bencodepy>=0.9.5",
        "urllib3>=2.5.0"
    ],
    packages=find_packages(),
    python_requires=">=3.6",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown"
)

# python setup.py sdist bdist_wheel
# twine upload dist/*