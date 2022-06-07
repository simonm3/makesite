"""Make static website with Python."""

import os
import shutil
import re
from glob import glob
import json
from datetime import datetime
import pandoc
from pandoc.types import Pandoc, Meta, Para
import logging
from defaultlog import log

log = logging.getLogger(__name__)

# Default parameters.
params = {
    "author": "Simon",
    "site_url": "http://localhost:8000",
    "current_year": datetime.now().year,
}


def fread(path):
    """Read file and close the file."""
    with open(path, "r") as f:
        return f.read()


def render(template, **context):
    """Replace placeholders in template with values from context."""
    return re.sub(
        r"{{\s*([^}\s]+)\s*}}",
        lambda match: str(context.get(match.group(1), match.group(0))),
        template,
    )


class Page:
    def __init__(self, path):
        self.path = path
        self.outpath = self.path.replace("content", "_site")
        self.outpath = f"{os.path.splitext(self.outpath)[0]}.html"

        self.pandoc = self.read()
        self.meta = self.getmeta()

    def read(self):
        return pandoc.read(file=self.path)

    def getmeta(self):
        meta = dict()

        # path metadata
        basename = os.path.basename(self.path)
        date_title, ext = os.path.splitext(basename)
        last_modified = os.stat(self.path).st_mtime
        last_modified = datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d")
        match = re.search(r"^(?:(\d\d\d\d-\d\d-\d\d)-)?(.+)$", date_title)
        meta["date"] = match.group(1) or last_modified
        meta["title"] = match.group(2)

        # doc metadata
        docmeta = {k: pandoc.write(v[0]).strip() for k, v in self.pandoc[0][0].items()}
        meta.update(docmeta)

        meta["rfc_2822_date"] = datetime.strptime(meta["date"], "%Y-%m-%d").strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )
        meta["relpath"] = "/".join(self.outpath.split("/")[1:])

        return meta

    def write(self, layout, **context):
        log.info(f"Rendering {self.path} => {self.outpath} ...")
        html = pandoc.write(self.pandoc, format="html")
        output = render(layout, content=html, **dict(context, **self.meta))
        os.makedirs(os.path.dirname(self.outpath), exist_ok=True)
        with open(f"{self.outpath}", "w") as f:
            f.write(output)
        return output


def write_index(pages, dst, list_layout, item_layout, **context):
    """Generate index page"""
    items = []
    for page in pages:
        try:
            # summary = first para, first 100 tokens
            summary = [x for x in page.pandoc[1] if isinstance(x, Para)][0][0][:100]
            summary = pandoc.write(Para(summary), format="html")
        except IndexError:
            summary = ""
        item = render(item_layout, summary=summary, **dict(context, **page.meta))
        items.append(item)

    log.info(f"Rendering index => {dst} ...")
    output = render(list_layout, content="".join(items), **context)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        f.write(output)
    return output


def main():
    # Create a new _site directory from scratch.
    if os.path.isdir("_site"):
        shutil.rmtree("_site")
    shutil.copytree("static", "_site")

    # If params.json exists, load it.
    if os.path.isfile("params.json"):
        params.update(json.loads(fread("params.json")))

    # Load layouts.
    page_layout = fread("layout/page.html")
    post_layout = fread("layout/post.html")
    list_layout = fread("layout/list.html")
    item_layout = fread("layout/item.html")
    feed_xml = fread("layout/feed.xml")
    item_xml = fread("layout/item.xml")

    # build layouts
    cats = [os.path.basename(c) for c in glob("content/*") if os.path.isdir(c)]
    menu = [f"<a href={category}>{category.capitalize()}</a>" for category in cats]
    menu = "\n".join(menu)
    page_layout = render(page_layout, menu=menu)
    post_layout = render(page_layout, content=post_layout)
    list_layout = render(page_layout, content=list_layout)

    # root pages (not indexed; page_layout)
    for src in [f for f in glob("content/*") if os.path.isfile(f)]:
        try:
            page = Page(src)
        except:
            log.exception(f"failed to read {src}")
            continue
        page.write(page_layout, **params)

    # categories (indexed; post_layout)
    for catpath in [f for f in glob("content/*") if os.path.isdir(f)]:
        # pages
        pages = []
        for src in glob(f"{catpath}/*"):
            try:
                page = Page(src)
            except:
                log.warning(f"failed to read {src}")
                continue
            page.write(post_layout, **params)
            pages.append(page)

        # index
        pages = sorted(pages, key=lambda x: x.meta["date"], reverse=True)
        catpath = catpath.replace("content", "_site")
        category = os.path.basename(catpath)
        context = dict(params, category=category, title=category)

        write_index(
            pages, f"{catpath}/index.html", list_layout, item_layout, **context,
        )
        # rss feed
        write_index(
            pages, f"{catpath}/rss.xml", feed_xml, item_xml, **context,
        )


# Test parameter to be set temporarily by unit tests.
_test = None

if __name__ == "__main__":
    main()

"""
Orisson
Zubiri

after zubiri
    Zariquiegui (before the hill)
    Uterga (after Camino do Perdon)
    Cirauqui
    Navarrete (las estrellas)
    Ciruena
    Granon (San Juan)
    Tosantos
    Villambistia
    San Juan de Ortega

after burgos
    Hornillos
    Castrojeriz
    Trabadelo
"""
