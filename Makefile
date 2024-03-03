# virtualenvs have hard coded absolute paths in them. Use a hash of pwd so you
# can run both make and circleci local execute, which has the project in a
# different path in the container. tox.ini uses it too so export.
PWD_HASH := $(shell pwd | $(shell command -v md5 md5sum | head -n 1) | awk '{print $$1}')
export PWD_HASH

build/test: test_fergalsiftttwebhooks.py fergalsiftttwebhooks.py build/venv-$(PWD_HASH)/bin/tox
	. build/venv-$(PWD_HASH)/bin/activate && tox
	touch build/test

build/venv-$(PWD_HASH)/bin/tox: build/venv-$(PWD_HASH)
	. build/venv-$(PWD_HASH)/bin/activate && pip install tox

build/venv-$(PWD_HASH):
	virtualenv build/venv-$(PWD_HASH)

build:
	mkdir build

clean:
	git clean -f -X -d

.PHONY: clean
