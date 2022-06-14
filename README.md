THIS IS STILL WORK IN PROGRESS

A simple blog site generator
============================

This is a simpler alternative to Jekyll, Pelican etc.. The core code is around 100 lines of python in a single file with the only dependencies being pandoc, tqdm and yatl

How to use
==========

1. Setup the repo
* Copy using clone or fork
* Enable github pages. Under Settings/Pages set source to gh-pages
2. Setup addins
* Setup Graphcomment, Googleanalytics and googlesearch
* Edit the appropriate layout file
3. Create content in the content folder
* Add subfolder for each category
* Add pages and media to the root folder or category folders
* Pages can be in any format supported by pandoc which includes md, rst, docx and ipynb 
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

Addins
======

* Posts allow comments via Graphcomment
* Metrics on site visits can be seen on googleanalytics
* Search box from google


Todo
====

* search. currently does not return any results.
* add thumbnail to index

Issues
======

pandoc
    ipynb
        OK images
        miss code formatting
        miss cells
    rst
        metadata treated as text
    docx
        loses formatted code in docx
    docx saved as html
        looks good as a page
        when added to page loses bullets and other characters

templates
    jinja2
        no anonymous include so need to redefine content pages with blocks
        restricted python e.g. list comprehension
    renoir
        cannot inject html
    yatl
        easy to miss the =
        no layout library




