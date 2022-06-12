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
from pandoc.types import *
from jinja2 import Environment, FileSystemLoader

from defaultlog import log

log = logging.getLogger(__name__)


def main():
    # global context
    gcontext = dict()
    gcontext["site_url"] = os.environ.get("MAKESITE_URL", "http://localhost:8000/")
    gcontext["current_year"] = datetime.now().year

    # site
    site = Site(gcontext)
    site.clear()
    cats = site.create_pages()
    site.create_indexes(cats)


class Site:
    def __init__(self, gcontext):
        self.outpath = "_site"
        self.gcontext = gcontext
        file_loader = FileSystemLoader("layout")
        self.env = Environment(loader=file_loader)

        cats = [os.path.basename(f) for f in glob("content/*") if os.path.isdir(f)]
        menu = [f"<a href={cat}>{cat.capitalize()}</a>" for cat in cats]
        menu = "\n".join(menu)
        self.gcontext.update(menu=menu)

    def clear(self):
        if os.path.isdir(self.outpath):
            shutil.rmtree(self.outpath)
        shutil.copytree("static", self.outpath)

    def create_pages(self):
        """ create the content pages. return index by category in format dict(cat=[meta, ...])"""
        cats = defaultdict(list)
        for src in tqdm(
            [f for f in glob("content/**", recursive=True) if os.path.isfile(f)]
        ):
            # copy media files etc..
            if os.path.splitext(src)[-1] not in pandoc._ext_to_file_format.keys():
                dst = src.replace("content/", f"{self.outpath}/")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(src, dst)
                continue

            # convert pages
            try:
                page = Page(src)
            except:
                log.exception(f"unable to parse {src}")
                continue

            html = pandoc.write(page.pandoc, format="html")
            context = dict(self.gcontext, content=html, **page.meta)
            if os.path.dirname(src) == "content":
                # root pages
                output = self.render("page.html", **context)
            else:
                # category pages use post layout and add meta to category index.
                output = self.render("post.html", **context)
                cats[page.meta["category"]].append(page.meta)
            self.write(output, page.meta["relpath"])
        return cats

    def create_indexes(self, cats):
        """ create category index pages and home index """
        for category, metas in cats.items():
            metas = sorted(metas, key=lambda meta: meta["date"], reverse=True)
            self.create_index(
                metas, category, **dict(title=category.capitalize(), **self.gcontext),
            )

        # home index page
        nposts = 10
        metas = list(itertools.chain(*cats.values()))
        metas = sorted(metas, key=lambda meta: meta["date"], reverse=True)[:nposts]
        self.create_index(
            metas, "", **dict(title=f"Most recent {nposts} posts", **self.gcontext)
        )

    def create_index(self, metas, path, **context):
        """Generate index page"""
        rsspath = "/".join([path, "rss.xml"])

        # write index
        metas_out = [
            self.render("item.html", **dict(context, **meta)) for meta in metas
        ]
        context = dict(context, content="".join(metas_out), rsspath=rsspath)
        output = self.render("list.html", **context)
        self.write(output, "/".join([path, "index.html"]))

        # write rss
        metas_out = [self.render("item.xml", **dict(context, **meta)) for meta in metas]
        context = dict(context, content="".join(metas_out), rsspath=rsspath)
        output = self.render("feed.xml", **context)
        self.write(output, rsspath)

    def write(self, output, dst):
        """ write file to site """
        dst = f"{self.outpath}/{dst}"
        log.debug(f"Writing {dst}")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w") as f:
            f.write(output)

    def render(self, template, **context):
        return self.env.get_template(template).render(**context)


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
        date_title, ext = os.path.splitext(os.path.basename(self.path))
        last_modified = os.stat(self.path).st_mtime
        last_modified = datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d")
        match = re.search(r"^(?:(\d\d\d\d-\d\d-\d\d)-)?(.+)$", date_title)
        meta["date"] = match.group(1) or last_modified
        meta["title"] = match.group(2)
        relpath = os.path.relpath(self.path, "content")
        meta["relpath"] = os.path.splitext(relpath)[0] + ".html"
        paths = meta["relpath"].split("/")
        meta["category"] = paths[0] if len(paths) > 0 else ""

        # doc metadata
        try:
            docmeta = self.meta2dict(self.pandoc)
            meta.update(docmeta)
        except:
            log.exception(f"unable to decode metadata for {self.path}")
        meta["rfc_2822_date"] = datetime.strptime(meta["date"], "%Y-%m-%d").strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )
        meta.setdefault("summary", "")

        return meta

    def meta2dict(self, meta):
        """ recursively convert pandoc metadata to dict """
        if isinstance(meta, (Pandoc, Meta, MetaMap)):
            return self.meta2dict(meta[0])
        elif isinstance(meta, dict):
            return {k: self.meta2dict(v) for k, v in meta.items()}
        elif isinstance(meta, MetaInlines):
            doc = [Para(meta[0])]
            return pandoc.write(doc).rstrip()
        elif isinstance(meta, MetaValue):
            return meta[0]

        raise Exception("Metadata type not found")


if __name__ == "__main__":
    main()
