# Copyright 2017 Palantir Technologies, Inc.
import os
import re
from urlparse import urlparse, urlunparse

# TODO: this is not the best e.g. we capture numbers
RE_START_WORD = re.compile('[A-Za-z_0-9]*$')
RE_END_WORD = re.compile('^[A-Za-z_0-9]*')


class Workspace(object):

    def __init__(self, root):
        self._url_parsed = urlparse(root)
        self.root = self._url_parsed.path
        self._docs = {}

    def is_local(self):
        return (self._url_parsed.scheme == '' or self._url_parsed.scheme == 'file') and os.path.exists(self.root)

    def get_document(self, doc_uri):
        self._check_in_workspace(doc_uri)
        return self._docs[doc_uri]

    def put_document(self, doc_uri, content):
        self._check_in_workspace(doc_uri)
        self._docs[doc_uri] = Document(doc_uri, content)

    def rm_document(self, doc_uri):
        self._docs.pop(doc_uri)

    def find_config_files(self, document, names):
        """ Find config files matching the given names relative to the given
        document looking in parent directories until one is found """
        curdir = os.path.dirname(document.path)

        while curdir != os.path.dirname(self.root) and curdir != '/':
            existing = filter(os.path.exists, [os.path.join(curdir, n) for n in names])
            if existing:
                return existing
            curdir = os.path.dirname(curdir)

    def get_uri_like(self, doc_uri, path):
        # Little bit hacky, but what' you gonna do
        parts = list(urlparse(doc_uri))
        parts[2] = path
        return urlunparse(parts)

    def _check_in_workspace(self, doc_uri):
        doc_path = urlparse(doc_uri).path
        if not os.path.commonprefix((self.root, doc_path)):
            raise ValueError("Document %s not in workspace %s" % (doc_uri, self.root))


class Document(object):

    def __init__(self, uri, source):
        self.uri = uri
        self.path = urlparse(self.uri).path
        self.filename = os.path.basename(self.path)
        self.source = source

    @property
    def lines(self):
        return self.source.splitlines(True)

    def word_at_position(self, position):
        """ Get the word under the cursor returning the start and end positions """
        line = self.lines[position['line']]
        i = position['character']
        # Split word in two
        start = line[:i]
        end = line[i:]

        # Take end of start and start of end to find word
        # These are guaranteed to match, even if they match the empty string
        m_start = RE_START_WORD.findall(start)
        m_end = RE_END_WORD.findall(end)

        return m_start[0] + m_end[-1]
