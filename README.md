THIS IS STILL WORK IN PROGRESS

A simple blog site generator
============================

This is a simpler alternative to Jekyll, Pelican etc.. The core code is around 100 lines of python in a single file with the only dependencies being pandoc and tqdm.

How to use
==========

1. Setup the repo
* Copy using clone or fork
* Enable github pages. Under Settings/Pages set source to gh-pages
2. Setup comments and analytics
* Create Graphcomment account and set siteid in layout/page.html
* Create a google analytics account and paste the appropriate code into layout/page.html
3. Create content in the content folder
* Add subfolder for each category
* Add pages and media to the root folder or category folders
* Pages can be in any format supported by pandoc which includes md, rst, docx and ipynb. 
* You can organize category folders into subfolders but all pages will appear under a single menu for the category.
4. Build and serve locally (localhost:8000)
* "make"
5. Build and serve on github pages (https://{username}.github.io/makesite/)
* "make publish" (add/commits/push changes to content folder)
* OR git push any changes to master branch

Features
========

* Home page shows index of latest articles across all categories plus rss feed
* Menu has buttons for root pages and categories
* Category home page shows index of articles in category plus rss feed
* Posts can be in any format supported by pandoc (md, rst, docx, ipynb etc..)
* Posts allow comments via Graphcomment
* Metrics on site visits can be seen on googleanalytics


Todo
====

* summary with image
* search
* Testing with notebooks
* soft code menu pages
* jinja2
    render only
    include + extends for page, googleanalytics and comments

Issues
======

* pandoc does not convert ipynb
* pandoc does not extract meta from rst





