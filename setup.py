import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Kkit",
    version="2.6.2",
    author="Erwin Li",
    author_email="erwinli@qq.com",
    description="some personnal kits",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/erwinliyh/Kylis_Kit",
    project_urls={
        "Bug Tracker": "https://github.com/erwinliyh/Kylis_Kit/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        "portalocker",
    ],
    extras_require={
        "color" : ["haishoku", "colorsys", "numpy", "requests"],
        "encryption" : ["cryptography"],
        "mder" : ["requests", "tqdm"],
        "scaling" : ["pandas"],
        "str2latex" : ["numpy"],
        "llm" : ["fastapi", "torch", "torchvision", "torchaudio", "uvicorn", "wandb",
                "transformers", "datasets", "peft", "python-multipart", "trl"],
        "doc" : ["pdoc"]
    },
    entry_points={
        'console_scripts': [
            'kkit-lora-server=Kkit.llm_utils.lora_fine_tune_server:main',
            'kkit-llamafactory-server=Kkit.llm_utils.llamafactory_server:main',
            'kkit-llama-server=Kkit.llm_utils.llamacpp_wrapper_server:main',
        ]
    }
)
