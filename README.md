THIS IS STILL WORK IN PROGRESS

A simple blog site generator
============================

This is a simpler alternative to Jekyll, Pelican etc.. The core code is around 100 lines of python code in a single file with the only dependencies being pandoc and tqdm.

How to use
==========

1. Setup the repo
* Copy using clone or fork
* Enable github pages. Under Settings/Pages set source to gh-pages
2. Create content in the content folder
* Add subfolder for each category
* Add pages and media to the root folder or category folders
* Pages can be in any format supported by pandoc which includes md, rst, docx and ipynb. 
* You can organize category folders into subfolders but all pages will appear under a single menu for the category.
3. Run "make" to serve locally (localhost:8000)
4. Run "make publish" to push content and serve on github pages (https://{username}.github.io/makesite/) Site will also be published automatically when pushing any changes to github.

Features
========

* Menu button to open each page in the root folder
* Menu button for each category that opens a category index page
* Category index pages link to articles in that folder plus an rss feed button
* Home page shows latest articles across all categories

* Metrics on site visits can be seen on googleanalytics. To enable this you need to create a google analytics account and paste the appropriate code into layout/page.html


Todo
====

* Comments
* Testing with notebooks

Issues
======

* pandoc does not convert ipynb
* pandoc does not extract meta from rst





