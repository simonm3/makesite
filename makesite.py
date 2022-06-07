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

ext2format = pandoc._ext_to_file_format

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


def fwrite(path, text):
    """Write page to file and close the file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def rfc_2822_format(date_str):
    """Convert yyyy-mm-dd date string to RFC 2822 format date string."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return d.strftime("%a, %d %b %Y %H:%M:%S +0000")


def render(template, **params):
    """Replace placeholders in template with values from params."""
    return re.sub(
        r"{{\s*([^}\s]+)\s*}}",
        lambda match: str(params.get(match.group(1), match.group(0))),
        template,
    )


def read_page(path):
    getmeta = lambda doc: {k: pandoc.write(v[0]).strip() for k, v in doc[0][0].items()}

    basename = os.path.basename(path)
    date_title, ext = os.path.splitext(basename)
    if ext not in ext2format.keys():
        log.warning(f"Unsupported file format: {path}")
        return None

    # path metadata
    last_modified = os.stat(path).st_mtime
    last_modified = datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d")
    match = re.search(r"^(?:(\d\d\d\d-\d\d-\d\d)-)?(.+)$", date_title)
    page = {
        "date": match.group(1) or last_modified,
        "title": match.group(2),
        "path": path,
    }

    # page
    page["pandoc"] = pandoc.read(file=path, format=ext2format[ext])

    # page metadata
    page.update(getmeta(page["pandoc"]))
    page["rfc_2822_date"] = rfc_2822_format(page["date"])

    return page


def write_page(page, layout, **params):
    """Generate page """
    page["content"] = pandoc.write(page["pandoc"], format="html")
    src = page["path"]
    dst = src.replace("content", "_site")
    dst = os.path.splitext(dst)[0] + ".html"
    page["outpath"] = "/".join(dst.split("/")[1:])
    page_params = dict(params, **page)

    output = render(layout, **page_params)

    log.info(f"Rendering {src} => {dst} ...")
    fwrite(dst, output)
    return output


def write_index(pages, dst, list_layout, item_layout, **params):
    """Generate index page"""
    items = []
    for page in pages:
        item_params = dict(params, **page)
        try:
            # summary = first para, first 100 tokens
            summary = [x for x in page["pandoc"][1] if isinstance(x, Para)][0][0][:100]
            summary = Para(summary)
            item_params["summary"] = pandoc.write(summary, format="html")
        except IndexError:
            item_params["summary"] = ""
        item = render(item_layout, **item_params)
        items.append(item)

    output = render(list_layout, content="".join(items), **params)

    log.info(f"Rendering index => {dst} ...")
    fwrite(dst, output)


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
        page = read_page(src)
        if page is None:
            continue
        write_page(page, page_layout, **params)

    # categories (indexed; post_layout)
    for category in [f for f in glob("content/*") if os.path.isdir(f)]:
        # pages
        pages = []
        for src in glob(f"{category}/*"):
            page = read_page(src)
            if page is None:
                continue
            write_page(page, post_layout, **params)
            pages.append(page)

        # index
        pages = sorted(pages, key=lambda x: x["date"], reverse=True)
        outpath = category.replace("content", "_site")
        category = os.path.basename(category)
        write_index(
            pages,
            f"{outpath}/index.html",
            list_layout,
            item_layout,
            category=category,
            title=category,
            **params,
        )
        # rss feed
        write_index(
            pages,
            f"{outpath}/rss.xml",
            feed_xml,
            item_xml,
            category=category,
            title=category,
            **params,
        )


# Test parameter to be set temporarily by unit tests.
_test = None


if __name__ == "__main__":
    main()
