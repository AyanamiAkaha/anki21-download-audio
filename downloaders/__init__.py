#!/usr/bin/env python
# -*- mode: python ; coding: utf-8 -*-
#
# Copyright © 2012–2014 Roland Sieker, <ospalh@gmail.com>
#
# License: GNU GPL, version 3 or later;
# http://www.gnu.org/copyleft/gpl.html

"""A list of audio downloaders.

They are intended for use with the Anki2 audiodownload add-on, but can
possibly be used alone. For each downloader in the list, setting its
language variable and then calling download_files(text, base, ruby,
split) downloads audio files to temp files and fills its
downloads_list with the file names.

When PyQt4 is installed, this downolads the site icon (favicon) for
each site first.
"""

from .google_tts import GooglettsDownloader
from .howjsay import HowJSayDownloader
from .japanesepod import JapanesepodDownloader
from .wiktionary import WiktionaryDownloader

downloaders = [
    JapanesepodDownloader(),
    HowJSayDownloader(),
    WiktionaryDownloader(),
    GooglettsDownloader(),
]
# This is the list of downloaders.
#
# These sites are tried in the order they appear here. Lines starting
# with a '#' are not tried. Change the order, or which lines get the
# '#' to taste


# # For testing.
# downloaders = [
#     DictNNDownloader(),
# ]

__all__ = ['downloaders']
