local: build serve

build:
	python makesite.py

serve:
	cd _site && python -m http.server

publish:
	git add content/*
	git commit -m "updated content"
	git push
