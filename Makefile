local: build serve

build:
	python makesite.py

serve:
	cd _site && python -m http.server
	

