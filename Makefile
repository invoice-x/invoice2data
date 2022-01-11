pypi-release:
	bumpversion patch
	# bumpversion minor
	git push upstream master
	git push upstream master --tags
	python setup.py sdist bdist_egg
	twine upload dist/invoice2data-0.3.6*
