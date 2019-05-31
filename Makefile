.PHONY:
	help
	buildclean
	pylintclean
	compileclean
	clean
	pylint
	pylint-reports
	dependencies
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
	@rm -Rf **/__pycache__
compileclean:
	@echo "Deleting compiled files"
	@rm -f **.pyc
	@rm -f **.pyo
clean: buildclean pylintclean compileclean

pylint:
	@pylint3 fragscapy; exit 0
pylint-reports:
	@pylint3 fragscapy --reports=y; exit 0

dependencies:
	pip3 install wheel
	pip3 install -r requirements.txt

installdev:
	./setup.py develop --uninstall
	./setup.py develop

install:
	./setup.py install

build: buildclean dependencies
	./setup.py sdist bdist_wheel
