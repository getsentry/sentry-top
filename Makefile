bootstrap:
	pip install -e .

bootstrap-tests:
	pip install pytest unittest2 exam mock pytest-django

test: bootstrap bootstrap-tests
	python runtests.py
