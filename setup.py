import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="niu",
    version="0.1.4",
    author="Matteo Bonora",
    author_email="bonora.matteo@gmail.com",
    description="NIU cloud interface library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Bonnee/niu",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.6",
)
