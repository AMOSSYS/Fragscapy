.PHONY: clean

buildclean:
	rm -Rf build
	rm -Rf dist
	rm -Rf fragscapy.egg-info
pylintclean:
	rm -Rf **/__pycache__
compileclean:
	rm -f **.pyc
	rm -f **.pyo
clean: buildclean pylintclean compileclean

pylint:
	pylint3 fragscapy
pylint-reports:
	pylint3 fragscapy --reports=y

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
