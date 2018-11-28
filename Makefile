pypi-release:
	bumpversion patch
	# bumpversion minor
	git push origin master
	git push origin master --tags
	python setup.py sdist bdist_egg
	twine upload dist/invoice2data-0.3.2*
