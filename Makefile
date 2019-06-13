.PHONY:
	help
	buildclean
	pylintclean
	compileclean
	docclean
	clean
	pylint
	pylint-reports
	pyreverse
	pyreverse-mod
	dependencies
	build
	install
	build-dev
	dependencies-dev
	install-dev
	dependencies-doc
	build-doc

# Help: display the main commands
help:
	@echo "Makefile for fragscapy. Most used commands:"
	@echo "  make install         install Fragscapy"
	@echo "  make install-dev     install Fragscapy in dev mode"
	@echo "  make build-doc       build the documentation"
	@echo "  make clean           cleanup the non-necessary files"
	@echo "  make pylint          evluate the code quality with pylint"
	@echo "  make pylint-reports  show the pylint reports"
	@echo "  make pyreverse       generate UML diagram of code without the mods"
	@echo "  make pyreverse-mod   generate UML diagram of code with the mods"

# Clean commands: clean different kind of files each
buildclean:
	@echo "Deleting build files"
	@rm -Rf build
	@rm -Rf dist
	@rm -Rf fragscapy.egg-info
pylintclean:
	@echo "Deleting pylint files"
	@find . -type d -path './fragscapy*/__pycache__' -exec rm -Rf {} +
compileclean:
	@echo "Deleting compiled files"
	@find . -type f -path './fragscapy/*.py[co]' -delete
docclean:
	@echo "Deleting documentation"
	@rm -rf docs/_build
	@find docs/source/ -not -path 'docs/source/' -not -path 'docs/source/_templates' -not -path 'docs/source/_templates/.placeholder' -not -path 'docs/source/index.rst' -not -path 'docs/source/conf.py' -not -path 'docs/source/_static' -not -path 'docs/source/_static/.placeholder' -print0 | xargs -0 rm -f --
clean: buildclean pylintclean compileclean docclean

# Pylint-related commands
pylint:
	@if ! command -v pylint; then echo "Pylint not found, run 'make dependencies-dev'."; exit 1; fi
	@pylint fragscapy; exit 0
pylint-reports:
	@if ! command -v pylint; then echo "Pylint not found, run 'make dependencies-dev'."; exit 1; fi
	@pylint fragscapy --reports=y; exit 0
pyreverse:
	@if ! command -v pyreverse; then echo "Pylint not found, run 'make dependencies-dev'."; exit 1; fi
	@pyreverse -p fragscapy $(find fragscapy/ -type f -not -path 'fragscapy/modifications/*') fragscapy/modifications/__init__.py fragscapy/modifications/mod.py fragscapy/modifications/utils.py
pyreverse-mod:
	@if ! command -v pyreverse; then echo "Pylint not found, run 'make dependencies-dev'."; exit 1; fi
	@pyreverse -p fragscapy fragscapy/

# Standard install
dependencies:
	pip3 install wheel
	pip3 install -r requirements.txt
build: buildclean dependencies
	./setup.py sdist bdist_wheel
install: build
	./setup.py install

# Development install
dependencies-dev: dependencies
	pip3 install wheel
	pip3 install -r requirements-dev.txt
build-dev: buildclean dependencies-dev
	./setup.py sdist bdist_wheel
install-dev: build-dev
	./setup.py develop --uninstall
	./setup.py develop

# Documentation building
dependencies-doc: dependencies
	pip3 install wheel
	pip3 install -r requirements-doc.txt
build-doc: dependencies-doc docclean
	mkdir docs/_build
	sphinx-apidoc -f -o docs/source fragscapy --separate
	sphinx-build -b html docs/source docs/_build
