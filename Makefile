RM=rm -rf

all: help

OSCAP_SOURCE=openscap-1.0.2.tar.gz
OSCAP_URL_PREFIX=http://fedorahosted.org/releases/o/p/openscap

help:
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets are:"
	@echo " help                    show this text"
	@echo " clean                   remove python bytecode and temp files"
	@echo " install                 install program on current system"
	@echo " log                     prepare changelog for spec file"
	@echo " source                  create source tarball"
	@echo " srpm                    create source rpm"
	@echo " rpm                     build latest version of preupgrade assistant package"
	#@echo " test                    run tests/run_tests.py"


clean-sdist-tarball:
	find -maxdepth 1 -type d -name 'preupgrade-assistant-*' -exec $(RM) {} +

clean: clean-sdist-tarball
	@python setup.py clean
	rm -f MANIFEST
	rm -rf *.src.rpm
	find . -\( -name "*.pyc" -o -name '*.pyo' -o -name "*~" -\) -delete


install:
	@python setup.py install


log:
	@(LC_ALL=C date +"* %a %b %e %Y `git config --get user.name` <`git config --get user.email`> - VERSION"; git log --pretty="format:- %s (%an)" | cat) | less


source: clean
	@python setup.py sdist -d .


srpm: source
	test -f ./$(OSCAP_SOURCE) || wget --no-check-certificate $(OSCAP_URL_PREFIX)/$(OSCAP_SOURCE)
	@rpmbuild -bs ./*.spec --define "_sourcedir ." --define "_specdir ." --define "_srcrpmdir ."


rpm: srpm
	@rpmbuild --rebuild ./*.src.rpm --define "_rpmdir ."

test:
	@python tests/test_preup.py
