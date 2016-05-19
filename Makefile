
# This GDCtools Makefile assumes presence of GNU Make, v3.8.1 or later

# -------------------------------------------------------------------------
#  							Variable definitions
# -------------------------------------------------------------------------

SHELL=/bin/bash
__FILE__=$(lastword $(MAKEFILE_LIST))
__PATH__=$(abspath $(dir $(__FILE__)))

EMAKE=$(MAKE) -e
TIMESTAMP = $(shell date +"%F %T")
REPO_HASH=$(shell $(GIT) log -n 1 --pretty=%H | cut -c 1-24)
VERSION = $(shell cat $(__PATH__)/VERSION)
LONGVERSION=$(VERSION) ($(TIMESTAMP) $(REPO_HASH))

PYTHON_HOME=$(shell ./config.sh)
DEST=$(PYTHON_HOME)
BIN_DIR=$(DEST)/bin					# Python virtual environment here
PYTHON=$(DEST)/bin/python
PIP=$(DEST)/bin/pip
#PYLINT = $(__PATH__)/pylint_wrap		# FIXME: code should be lint-ed

TOOLS= \
	gdc_mirror

CORE_SRC_FILES=\
	GDCcli.py \
	GDCutils.py

PKG_SRC_FILES=\
	$(CORE_SRC_FILES) \
	$(TOOLS:%=%.py) \
	tictoc.py

PKG_SRC_NAMES=$(PKG_SRC_FILES:%.py=%)
LINKS=$(TOOLS:%=bin/%)
RUNPY=bin/runpy
GENERATED_STUFF = gdctools.py GDCutils.py README

# -------------------------------------------------------------------------
#							General Targets
# -------------------------------------------------------------------------

default: bin $(RUNPY) $(LINKS) $(GENERATED_STUFF)

help:
	@echo "Type:"
	@echo "	make              to create links for simple use from this dev tree"
	@echo "	make install      for production install to $(DEST)"

clean:
	\rm -rf *~ *.pyc __pycache__ $(STAGING_DIR) bin $(GENERATED_STUFF)

.PHONY: default help test test3 clean install uninstall pypi FORCE

# -------------------------------------------------------------------------
#							Building & Packaging
# -------------------------------------------------------------------------

$(RUNPY): runpy.ac
	@mkdir -p bin
	sed 's|%PYTHON%|$(PYTHON)|' runpy.ac > $@
	chmod +x $@

$(LINKS): $(RUNPY)
	\rm -f $@
	ln -s runpy $@

PKG_NAME=gdctools
STAGING_DIR=build
PKG_DIR=$(STAGING_DIR)/$(PKG_NAME)
METAFILES=setup.ac LICENSE.txt README

install:  gather
	cd $(STAGING_DIR) ; \
	$(PIP) install --upgrade .
	@echo

gather: default $(STAGING_DIR) Makefile $(PKG_SRCFILES) $(METAFILES)
	$(EMAKE) dir_exists DIR=DEST
	\rm -rf $(PKG_DIR) ; \
	mkdir -p $(PKG_DIR) ; \
	cp -fp $(PKG_SRC_FILES) $(PKG_DIR)/. ;\
	$(EMAKE) $(PKG_DIR)/__init__.py ;\
	cp -fp $(METAFILES) $(STAGING_DIR)/. ; \
	cd $(STAGING_DIR) ; \
	sed "s/%VERSION%/\"$(VERSION)\"/" setup.ac > setup.py

uninstall:
	$(PIP) uninstall --yes $(PKG_NAME)

$(PKG_DIR)/__init__.py: FORCE
	\rm -f $@
	for tool in $(PKG_SRC_NAMES) ; do \
		echo "from .$$tool import *"  >> $@ ; \
	done
	cat console.py >> $@

gdctools.py:
	@# Generate script for use locally in the dev tree, providing the ability
	@# to "import gdctools" as if the package were properly installed.  This
	@# script should NOT be bundled into any pkgs built for gdctools proper.
	@# The import stmts s/b effectively identical to those in __init__.py
	@echo > $@
	@for file in $(PKG_SRC_FILES) ; do \
		echo "import `basename $$file .py`"  >> $@ ; \
	done

GDCutils.py: GDCutils.py.ac
	sed "s/%VERSION%/$(VERSION)/" $@.ac > $@

#pypi: gather
#	cd $(STAGING_DIR) ; \
#	$(PYTHON) setup.py sdist upload

$(STAGING_DIR) bin:
	mkdir -p $@

dir_exists:
	@if [ ! -d "$($(DIR))" ] ; then \
		echo "Error: $(DIR) undefined or points to non-existent dir: $($(DIR))" ;\
		false ; \
	fi

FORCE:

README: README.md
	cp -f $? $@

# -------------------------------------------------------------------------
#								Testing
# -------------------------------------------------------------------------
#
# Tests are currently very simple, at the level of a smoketest

test: default
	@# Basic test in local directory
	@ $(PYTHON) GDCcli.py
	@echo
	$(PYTHON) GDCtool.py

test3:
	@# Python 3 compatibility
	@. /broad/tools/scripts/useuse && \
		reuse -q Python-3.4 && \
		$(MAKE) -e test

testi:
	@# Test the installed package
	(cd /tmp ; $(PYTHON) -c "from gdctools import *; print('Version: ' + GDCT_version) ")
