"""Make static website with Python."""

import os
import shutil
import re
from glob import glob
from datetime import datetime
from collections import defaultdict
import itertools
import logging

from tqdm.auto import tqdm
import pandoc

from defaultlog import log

log = logging.getLogger(__name__)


def main():
    # initialise _site
    if os.path.isdir("_site"):
        shutil.rmtree("_site")
    shutil.copytree("static", "_site")

    # global context
    gcontext = dict()
    gcontext["site_url"] = os.environ.get("MAKESITE_URL", "http://localhost:8000/")
    gcontext["current_year"] = datetime.now().year

    # create layouts
    layouts = Layouts()
    layouts.load()
    layouts.build()

    # content pages
    cats = defaultdict(list)
    for src in tqdm(
        [f for f in glob("content/**", recursive=True) if os.path.isfile(f)]
    ):
        try:
            page = Page(src)
        except:
            log.exception(f"failed to read {src}")
            continue
        if os.path.dirname(src) == "content":
            # root pages
            page.write(layouts.page, **gcontext)
        else:
            # category pages use post layout and add meta to category index.
            page.write(layouts.post, **gcontext)
            cats[page.meta["category"]].append(page.meta)

    # category index pages
    index = Index(layouts)
    for category, items in cats.items():
        items = sorted(items, key=lambda item: item["date"], reverse=True)
        index.write(
            items, category, **dict(title=category.capitalize(), **gcontext),
        )

    # home index page
    items = list(itertools.chain(*cats.values()))
    items = sorted(items, key=lambda item: item["date"], reverse=True)[:10]
    index.write(items, "", **dict(title="Recent posts", **gcontext))


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

    def write(self, layout, **gcontext):
        relpath = self.meta["relpath"]
        html = pandoc.write(self.pandoc, format="html")
        context = dict(gcontext, content=html, **self.meta)
        output = render(layout, **context)
        fwrite(output, relpath)


class Layouts:
    def __setitem__(self, k, v):
        setattr(self, k, v)

    def load(self):
        for path in glob("layout/*"):
            x = os.path.basename(path)
            name, ext = os.path.splitext(x)
            name = name if ext == ".html" else name + ext.lstrip(".")
            self[name] = fread(path)

    def build(self):
        cats = [
            os.path.basename(c)
            for c in glob("content/**", recursive=True)
            if os.path.isdir(c)
        ]
        menu = [f"<a href={category}>{category.capitalize()}</a>" for category in cats]
        menu = "\n".join(menu)
        self.page = render(self.page, menu=menu)
        self.post = render(self.page, content=self.post)
        self.list = render(self.page, content=self.list)


class Index:
    def __init__(self, layouts):
        self.layouts = layouts

    def write(self, items, path, **gcontext):
        """Generate index page"""
        lay = self.layouts
        rsspath = "/".join([path, "rss.xml"])

        # write index
        items_out = [render(lay.item, **dict(gcontext, **item)) for item in items]
        output = render(
            lay.list, content="".join(items_out), rsspath=rsspath, **gcontext
        )
        fwrite(output, "/".join([path, "index.html"]))

        # write rss
        items_out = [render(lay.itemxml, **dict(gcontext, **item)) for item in items]
        output = render(
            lay.feedxml, content="".join(items_out), rsspath=rsspath, **gcontext
        )
        fwrite(output, rsspath)


######################################################################


def fread(path):
    """Read file and close the file."""
    with open(path, "r") as f:
        return f.read()


def fwrite(output, dst):
    """ write file """
    dst = f"_site/{dst}"
    log.debug(f"Writing {dst}")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        f.write(output)


def render(template, **context):
    """Replace placeholders in template with values from context."""
    return re.sub(
        r"{{\s*([^}\s]+)\s*}}",
        lambda match: str(context.get(match.group(1), match.group(0))),
        template,
    )


if __name__ == "__main__":
    main()
