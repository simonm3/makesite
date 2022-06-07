site:
	python makesite.py

serve: site
	cd _site && python -m http.server
	
venv2:
	virtualenv ~/.venv/makesite
	echo . ~/.venv/makesite/bin/activate > venv
	. ./venv && pip install pandoc coverage

venv: FORCE
	python3 -m venv ~/.venv/makesite
	echo . ~/.venv/makesite/bin/activate > venv
	. ./venv && pip install pandoc coverage

test: FORCE
	. ./venv && python -m unittest -bv

coverage:
	. ./venv && coverage run --branch --source=. -m unittest discover -bv; :
	. ./venv && coverage report -m
	. ./venv && coverage html

clean:
	find . -name "__pycache__" -exec rm -r {} +
	find . -name "*.pyc" -exec rm {} +
	rm -rf .coverage htmlcov

REV = cat /tmp/rev.txt
example:
	#
	# Remove existing output directories.
	rm -rf _site /tmp/_site
	#
	# Create params.json for makesite-demo.
	echo '{ "base_path": "/makesite-demo", "site_url":' \
	     '"https://tmug.github.io/makesite-demo" }' > params.json
	#
	# Generate the website.
	. ./venv && ./makesite.py
	rm params.json
	#
	# Get current commit ID.
	git rev-parse --short HEAD > /tmp/rev.txt
	#
	# Write a README for makesite-demo repository.
	echo makesite.py demo > _site/README.md
	echo ================ >> _site/README.md
	echo This is the HTML/CSS source of an example static >> _site/README.md
	echo website auto-generated with [sunainapai/makesite][makesite] >> _site/README.md
	echo "([$$($(REV))][commit])". >> _site/README.md
	echo >> _site/README.md
	echo Visit "<https://tmug.github.io/makesite-demo>" to >> _site/README.md
	echo view the example website. >> _site/README.md
	echo >> _site/README.md
	echo [makesite]: https://github.com/sunainapai/makesite >> _site/README.md
	echo [commit]: https://github.com/sunainapai/makesite/commit/$$($(REV)) >> _site/README.md
	echo [demo]: https://tmug.github.io/makesite-demo >> _site/README.md
	#
	# Publish makesite-demo.
	mv _site /tmp
	cd /tmp/_site && git init
	cd /tmp/_site && git config user.name Makesite
	cd /tmp/_site && git config user.email makesite@example.com
	cd /tmp/_site && git add .
	cd /tmp/_site && git commit -m "Auto-generated with sunainapai/makesite - $$($(REV))"
	cd /tmp/_site && git remote add origin https://github.com/tmug/makesite-demo.git
	cd /tmp/_site && git log
	cd /tmp/_site && git push -f origin master

loc:
	grep -vE '^[[:space:]]*#|^[[:space:]]*$$|^[[:space:]]*"""' makesite.py | wc -l

FORCE:
