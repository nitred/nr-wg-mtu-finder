.DEFAULT_GOAL := help

help:             ## Show available options with this Makefile
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

.PHONY : test
test:             ## Run all the tests
test:
	python setup.py test

.PHONY : recreate_pyenv
recreate_pyenv:   ## Create the python environment. Recreates if the env exists already.
recreate_pyenv:
	conda env create --force -f dev_environment.yml

.PHONY : readme_to_rst
readme_to_rst:    ## Convert README.md to README.rst for the sake of pip documentation.
readme_to_rst:
	m2r --overwrite README.md

.PHONY : upload_test_pypi
upload_test_pypi: ## Build and upload distribution to testpypi server
upload_test_pypi: readme_to_rst
	python setup.py bdist_wheel --dist-dir dist && \
	twine upload --skip-existing --repository testpypi dist/*

.PHONY : upload_pypi
upload_pypi:      ## Build and upload distribution to pypi server
upload_pypi: readme_to_rst
	python setup.py bdist_wheel --dist-dir dist && \
	twine upload --skip-existing --repository pypi dist/*

.PHONY : lint
lint:             ## Run flake8 linter
lint:
	flake8 nr_pypackage
