.PHONY:
	help
	buildclean
	pylintclean
	compileclean
	docclean
	clean
	pylint
	pylint-reports
	dependencies
	dependencies-doc
	build-doc
	installdev
	install
	build

help:
	@echo "Makefile for fragscapy. Most used commands:"
	@echo "  make build"
	@echo "  make install"
	@echo "  make installdev"
	@echo "  make clean"
	@echo "  make pylint"
	@echo "  make pylint-reports"

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

pylint:
	@pylint3 fragscapy; exit 0
pylint-reports:
	@pylint3 fragscapy --reports=y; exit 0

dependencies:
	pip3 install wheel
	pip3 install -r requirements.txt

dependencies-doc: dependencies
	pip3 install wheel
	pip3 install -r requirements-doc.txt

build-doc: dependencies-doc docclean
	mkdir docs/_build
	sphinx-apidoc -f -o docs/source fragscapy --separate
	sphinx-build -b html docs/source docs/_build

installdev:
	./setup.py develop --uninstall
	./setup.py develop

install:
	./setup.py install

build: buildclean dependencies
	./setup.py sdist bdist_wheel
