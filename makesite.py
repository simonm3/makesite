"""Make static website with Python."""

import os
import shutil
import re
from glob import glob
from datetime import datetime
from collections import defaultdict
import itertools
import logging

import pandoc

from defaultlog import log

log = logging.getLogger(__name__)


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
        meta["relpath"] = os.path.relpath(self.path, "content")
        meta["relpath"] = os.path.splitext(meta["relpath"])[0] + ".html"
        try:
            meta["category"] = meta["relpath"].split("/")[-2]
        except IndexError:
            meta["category"] = None

        # doc metadata
        docmeta = {k: pandoc.write(v[0]).strip() for k, v in self.pandoc[0][0].items()}
        meta.update(docmeta)

        meta["rfc_2822_date"] = datetime.strptime(meta["date"], "%Y-%m-%d").strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )
        meta.setdefault("summary", "")

        return meta

    def write(self, layout, **context):
        relpath = self.meta["relpath"]
        outpath = f"_site/{relpath}"
        log.info(f"Rendering {self.path} => {outpath} ...")
        html = pandoc.write(self.pandoc, format="html")
        output = render(layout, content=html, **dict(context, **self.meta))
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(f"{outpath}", "w") as f:
            f.write(output)
        return output


def write_index(items, dst, list_layout, item_layout, **context):
    """Generate index page"""
    items = [render(item_layout, **dict(context, **item)) for item in items]

    log.info(f"Rendering index => {dst} ...")
    output = render(list_layout, content="".join(items), **context)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        f.write(output)
    return output


def main():
    # initialise _site
    if os.path.isdir("_site"):
        shutil.rmtree("_site")
    shutil.copytree("static", "_site")

    # global context
    context = dict()
    context["site_url"] = os.environ.get("MAKESITE_URL", "http://localhost:8000/")
    context["current_year"] = datetime.now().year

    # Load layouts
    class Layouts:
        def __init__(self):
            for x in glob("layout/*"):
                x = os.path.basename(x)
                name, ext = os.path.splitext(x)
                name = name if ext==".html" else name + ext.lstrip(".")
                self[name] = fread(x)

    page_layout = fread("layout/page.html")
    post_layout = fread("layout/post.html")
    list_layout = fread("layout/list.html")
    item_layout = fread("layout/item.html")
    feed_xml = fread("layout/feed.xml")
    item_xml = fread("layout/item.xml")

    # build layouts
    cats = [
        os.path.basename(c)
        for c in glob("content/**", recursive=True)
        if os.path.isdir(c)
    ]
    menu = [f"<a href={category}>{category.capitalize()}</a>" for category in cats]
    menu = "\n".join(menu)
    page_layout = render(page_layout, menu=menu)
    post_layout = render(page_layout, content=post_layout)
    list_layout = render(page_layout, content=list_layout)

    # write content pages
    cats = defaultdict(list)
    for src in [f for f in glob("content/**", recursive=True) if os.path.isfile(f)]:
        try:
            page = Page(src)
        except:
            log.exception(f"failed to read {src}")
            continue
        paths = os.path.relpath(src, "content").split("/")
        if page.meta["category"] is None:
            # root pages
            page.write(page_layout, **context)
        else:
            # category pages use post layout and add meta to category index.
            page.write(post_layout, **context)
            cats[page.meta["category"]].append(page.meta)

    # write category index pages and rss
    for category, items in cats.items():
        items = sorted(items, key=lambda item: item["date"], reverse=True)
        write_index(
            items,
            f"_site/{category}/index.html",
            list_layout,
            item_layout,
            **dict(category=category, title=category, **context),
        )
        write_index(
            items,
            f"_site/{category}/rss.xml",
            feed_xml,
            item_xml,
            **dict(category=category, title=category, **context),
        )

    # write index page
    items = list(itertools.chain(*cats.values()))
    items = sorted(items, key=lambda item: item["date"], reverse=True)[:5]
    write_index(
        items,
        f"_site/index.html",
        list_layout,
        item_layout,
        **dict(title="Recent posts", **context),
    )


if __name__ == "__main__":
    main()


"""
layouts class
combine xml and html
"""
