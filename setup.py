from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="pb_plant_maintenance",
    version="1.0.0",
    description="Plant Maintenance Custom Module for ERPNext by Processbricks",
    author="Processbricks",
    author_email="venkatnarasimha@processbricks.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)