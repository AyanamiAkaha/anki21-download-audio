# -*- mode: python; coding: utf-8 -*-
#
# Copyright © 2012–2013 Roland Sieker, ospalh@gmail.com
#
# License: GNU AGPL, version 3 or later;
# http://www.gnu.org/copyleft/agpl.html


'''
Class to download a files from a speaking dictionary or TTS service.
'''

import tempfile
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import urllib.parse
from bs4 import BeautifulSoup as soup
from aqt.utils import showInfo

DEBUG = None

# Make this work without PyQt
with_pyqt = True
try:
    from PyQt5.QtGui import QImage
    from PyQt5.QtCore import QSize, Qt
except ImportError:
    with_pyqt = False


def uniqify_list(seq):
    """Return a copy of the list with every element appearing only once."""
    # From http://www.peterbe.com/plog/uniqifiers-benchmark
    no_dupes = []
    [no_dupes.append(i) for i in seq if not no_dupes.count(i)]
    return no_dupes


class AudioDownloader(object):
    """
    Class to download a files from a dictionary or TTS service.

    This is the base class for the downloaders of spoken
    pronunciations.

    The derived classes must implement self.download_files()
    """
    def __init__(self):
        self.language = ''
        """
        The language used.

        This is used as a public variable and set for every download.
        """
        self.downloads_list = []
        """
        Store for downloaded data.

        This is where self.download_files should store the
        results. See that method's docstring.
        """
        self.display_text = ''
        """Text shown as source after download"""
        self.base_name = ''
        """Base of the final file name."""
        self.file_extension = '.wav'
        # A typical downloaders will need something like this.
        self.url = ''
        """The base URL used for (the first step of) the download."""
        self.icon_url = ''
        """URL to get the address of the site icon from."""
        self.max_icon_size = 20
        """Max size we scale the site icon down to, if larger."""
        self.user_agent = 'Mozilla/5.0'
        """
        User agent string that can be used for requests.

        At least Google TTS won't give out their translations unless
        we pretend to be some typical browser.
        """
        self.use_temp_files = False
        """
        Whether to use files created by tempfiles or not.

        Where to write the downloaded files, in /tmp/ or into the Anki
        media directory directly.
        """
        # This is set to True by the "real" audio processor that does
        # normalization but doesn't work for standard installs. On
        # typical installs this is kept False.)

        self.download_directory = None
        """
        Where to write the downloaded files.

        If this is None or empty
        (i.e. "if not self.download_directory:...")
        (and self.use_temp_files == False)
        we use the current directory.
        """
        self.show_skull_and_bones = False
        """
        Should we show the skull and crossbones in the review dialog?

        Normal downloaders should leave this alone. The point of the
        whole blacklist mechanism is that JapanesePod can't say
        no. Only when there is a chance that we have a file we want to
        blacklist (that is, when we actually downloaded something from
        Japanesepod) should we set this to True.
        """

        self.site_icon = None
        """The sites's favicon."""

    def download_files(self, word, base, ruby, split):
        """
        Downloader functon.

        This is the main worker function. It has to be reimplemented
        by the derived classes.

        The input is the text to use for the download, either the
        whole text (for most languages) or split into kanji and kana,
        base and ruby.

        This function should clear the self.downloads_list, call
        self.set_names(), and try to get pronunciation files from its
        source, put those into tempfiles, and add a (temp_file_path,
        base_name, extras) 3-tuple to self_downloads_lists for each of
        the zero or more downloaded files. (Zero when the
        self.language is wrong, there is no file, ...) extras should
        be a dict with strings of interesting informations, like
        meaning numbers or name of speaker, or an empty dict.
        """
        raise NotImplementedError("Use a class derived from this.")

    def set_names(self, text, dummy_base, dummy_ruby):
        """
        Set the display text and file base name variables.

        Set self.display_text and self.base_name with the text used
        for download, formated in a form useful for display and for a
        file name, respectively.
        This version uses just the text. It should be reimplemented
        for Japanese (Chinese, ...)  downloaders that use the base and
        ruby.
        """
        self.base_name = text
        self.display_text = text

    def maybe_get_icon(self):
        """
        Get icon for the site as a QImage if we haven't already.

        Get the site icon, either the 'rel="icon"' or the favicon, for
        the web page at url or passed in as page_html and store it as
        a QImage. This function can be called repeatedly and loads the
        icon only once.
        """
        if self.site_icon:
            return
        if not with_pyqt:
            self.site_icon = None
            return
        page_request = urllib.request.Request(self.icon_url)
        if self.user_agent:
            page_request.add_header('User-agent', self.user_agent)
        page_response = urllib.request.urlopen(page_request)
        if 200 != page_response.code:
            self.get_favicon()
            return
        page_soup = soup(page_response, "html.parser")
        try:
            icon_url = page_soup.find(
                name='link', attrs={'rel': 'icon'})['href']
        except (TypeError, KeyError):
            self.get_favicon()
            return
        # The url may be absolute or relative.
        if not urllib.parse.urlsplit(icon_url).netloc:
            icon_url = urllib.parse.urljoin(
                self.url, urllib.parse.quote(icon_url))
        try:
            icon_request = urllib.request.Request(icon_url)
            if self.user_agent:
                icon_request.add_header('User-agent', self.user_agent)
            icon_response = urllib.request.urlopen(icon_request)
            if 200 != icon_response.code:
                self.site_icon = None
                return
        except urllib.error.URLError as ex:
            if DEBUG:
                showInfo("URL error for '%s': %s" % (icon_url, ex))
            return
        self.site_icon = QImage.fromData(icon_response.read())
        max_size = QSize(self.max_icon_size, self.max_icon_size)
        icon_size = self.site_icon.size()
        if icon_size.width() > max_size.width() \
                or icon_size.height() > max_size.height():
            self.site_icon = self.site_icon.scaled(
                max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def get_favicon(self):
        """
        Get favicon for the site.

        This is called when the site_url can't be loaded or when that
        page doesn't contain a link tag with rel set to icon (the new
        way of doing site icons.)
        """
        if self.site_icon:
            return
        if not with_pyqt:
            self.site_icon = None
            return
        ico_url = urllib.parse.urljoin(self.icon_url, "/favicon.ico")
        ico_request = urllib.request.Request(ico_url)
        if self.user_agent:
            ico_request.add_header('User-agent', self.user_agent)
        ico_response = urllib.request.urlopen(ico_request)
        if 200 != ico_response.code:
            self.site_icon = None
            return
        self.site_icon = QImage.fromData(ico_response.read())
        max_size = QSize(self.max_icon_size, self.max_icon_size)
        ico_size = self.site_icon.size()
        if ico_size.width() > max_size.width() \
                or ico_size.height() > max_size.height():
            self.site_icon = self.site_icon.scaled(
                max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def get_data_from_url(self, url_in):
        """
        Return raw data loaded from an URL.

        Helper function. Put in an URL and it sets the agent, sends
        the requests, checks that we got error code 200 and returns
        the raw data only when everything is OK.
        """
        # try:
        #     # There have been reports that the request was send in a
        #     # 32-bit encoding (UTF-32?). Avoid that. (The whole things
        #     # is a bit curious, but there shouldn't really be any harm
        #     # in this.)
        #     if DEBUG:
        #         showInfo(url_in)
        #     request = urllib.request.Request(url_in.encode('utf-8'))
        # except UnicodeDecodeError:
        #     request = urllib.request.Request(url_in)
        # try:
        #     # dto. But i guess this is even less necessary.
        #     request.add_header('User-agent', self.user_agent.encode('utf-8'))
        # except UnicodeDecodeError:
        #     request.add_header('User-agent', self.user_agent)
        request = urllib.request.Request(url_in)
        request.add_header('User-agent', self.user_agent)
        response = urllib.request.urlopen(request)
        if 200 != response.code:
            raise ValueError(str(response.code) + ': ' + response.msg)
        return response.read()

    def get_soup_from_url(self, url_in):
        """
        Return data loaded from an URL, as BeautifulSoup(3) object.

        Wrapper helper function aronud self.get_data_from_url()
        """
        return soup(self.get_data_from_url(url_in), "html.parser")

    def get_file_name(self):
        """
        Get a free file name.

        Determine where we should write the data and build a free name
        based on that. This looks at self.use_temp_files and
        self.download_diretory. Read their docstrings.
        """
        if self.use_temp_files:
            tfile = tempfile.NamedTemporaryFile(
                delete=False, suffix=self.file_extension)
            tfile.close()
            # Hack, free_media_name returns full path and file name,
            # so return two files here as well. But there is no real
            # need to split off the file name from the direcotry bit.
            return tfile.name, tfile.name
        else:
            # IAR, specifically PEP8. When we don't use temp files, we
            # should clean up the request string a bit, and that is
            # best done with Anki functions. So, when
            # self.use_temp_files is False, we need anki, bits of
            # which are imported by ..exists.
            from ..exists import free_media_name
            return free_media_name(
                self.base_name, self.file_extension)
