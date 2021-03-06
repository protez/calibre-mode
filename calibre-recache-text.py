
from __future__ import (print_function)
import os, sys
CALIBRE_SRC_DIR = os.path.expanduser("~/dev/calibre/calibre-src")
sys.path.append(os.path.join(CALIBRE_SRC_DIR, "src"))
sys.resources_location = os.environ.get('CALIBRE_RESOURCES_PATH', os.path.join(CALIBRE_SRC_DIR, "resources"))
sys.extensions_location = os.environ.get('CALIBRE_EXTENSIONS_PATH', os.path.join(CALIBRE_SRC_DIR, "src/calibre/plugins"))
sys.executables_location = os.environ.get('CALIBRE_EXECUTABLES_PATH', '/usr/bin')

import string
import shelve
import subprocess
from calibre import as_unicode
from calibre.ebooks.metadata import check_isbn
from calibre.ebooks.metadata.sources.base import Source
from calibre.utils.icu import lower
from calibre.utils.cleantext import clean_ascii_chars
from calibre.utils.localization import get_udc
from calibre.customize.ui import *
from calibre.ebooks.metadata.book.base import Metadata

from calibre.library import cli

class Dummy: library_path=os.path.expanduser("~/Calibre Library/")

cdb = cli.get_db(os.path.join(Dummy.library_path, "metadata.db"), Dummy())

def make_citekey(dcbk):
    return "%s%sid%s" % (dcbk["author_sort"].split("&")[0].split(",")[0].replace(" ", "").replace("?", ""), dcbk["pubdate"].year, dcbk["id"])

#D = shelve.open("calibre.shelve")
#D.close()

tpl_text = string.Template("""#+TITLE: $TITLE
  $AUTHORLIST

$FILEPATH

* $CITEKEY
  $TAGLIST
  $KEYWORDLIST
  $PROJECTLIST

* [[file:note.org][note file]]

* text

$TEXT
""")

tpl_note = string.Template("""#+TITLE: $TITLE

  ($CITEKEY) [[file:text.org][article text file]]

* note

  
""")

OUTPUT_NOTE_FILE = False # create a 'note.org' file in the cache text directory; disabled because I realized I don't use it at all
OVERWRITE = False
OUTPUTDIR = os.path.expanduser("~/note/org/calibre")
output_count = 0
lsdcbk = cdb.get_data_as_dict()
if True:
    for dcbk in lsdcbk:
        citekey = make_citekey(dcbk)
        out_book_dir = os.path.join(OUTPUTDIR, citekey)
        if not os.path.exists(out_book_dir):
            os.mkdir(out_book_dir)
        out_text_filepath = os.path.join(out_book_dir, "text.org")
        out_note_filepath = os.path.join(out_book_dir, "note.org")
        articletext = ""
        if "fmt_pdf" in dcbk:
            p = subprocess.Popen(["pdftotext", dcbk["fmt_pdf"], "-"], stdout=subprocess.PIPE)
            articletext = p.stdout.read()
        writeoption = None
        if not os.path.exists(out_text_filepath) or OVERWRITE:
            with open(out_text_filepath, "w") as ofile:
                dproj = dcbk[cdb.custom_column_label_map["project"]['num']]
                dkeyword = dcbk[cdb.custom_column_label_map["keywords"]['num']]
                ls_project = dproj and dproj.split("|") or []
                ls_keyword = dkeyword and dkeyword.split("|") or []
                ofile.write(tpl_text.substitute(TITLE = dcbk["title"],
                                                FILEPATH = "\n".join(map(lambda fpath: "- %s: [[file:%s]]" % (os.path.splitext(fpath)[-1][1:].upper(), fpath), dcbk["formats"])),
                                                AUTHORLIST = " ; ".join(dcbk["authors"]),
                                                PROJECTLIST = ", ".join(ls_project),
                                                KEYWORDLIST = ", ".join(ls_keyword),
                                                CITEKEY = citekey,
                                                TEXT = articletext,
                                                TAGLIST = dcbk["tags"] and "        :%s:" % ":".join(dcbk["tags"]) or ""))
            output_count += 1
            print("wrote: %s" % ofile.name)  
        if OUTPUT_NOTE_FILE:
            if not os.path.exists(out_note_filepath):
                with open(out_note_filepath, "w") as ofile:
                    ofile.write(tpl_note.substitute(TITLE = dcbk["title"],
                                                    CITEKEY = citekey))
                print("wrote: %s" % ofile.name)  

    print("%s outputted" % output_count)
if not True:
    def getlist(dc, key):
        val = dc[cdb.custom_column_label_map[key]['num']]
        if val: return val.lower().split("|")
        else: return []

    for dcbk in lsdcbk:
        keywordlist = getlist(dcbk, "keywords")
        projectlist = getlist(dcbk, "project")
        if "st" in keywordlist or "st" in projectlist:
            print(make_citekey(dcbk))
