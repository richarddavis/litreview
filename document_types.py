class Doc():
    valid_doctypes = ["papers", "notebooks"]
    def __init__(self, doctype="docs", title=None, authors=None, year=None, doi=None, inlinks=[], outlinks=[], id=None):
        self.doctype = doctype
        self.title = title
        self.authors = authors
        self.year = year
        if self.year is not None:
            self.year = int(year)
        self.doi = doi
        if self.doi is not None:
            self.doi = doi.lower()
        self.inlinks = inlinks
        self.outlinks = outlinks
        self.id = id

    @staticmethod
    def from_ref(ref):
        source = ref.to_dict()
        doc = Doc(doctype=source[u'doctype'], \
                  title=source[u'title'], \
                  authors=source[u'authors'], \
                  id=ref.id)

        if u'year' in source:
            doc.year = source[u'year']

        if u'doi' in source:
            doc.doi = source[u'doi']

        if u'inlinks' in source:
            doc.inlinks = source[u'inlinks']

        if u'outlinks' in source:
            doc.outlinks = source[u'outlinks']

        return doc

    def to_dict(self):
        doc = {
            u'doctype':self.doctype,
            u'title': self.title,
            u'authors': self.authors,
        }

        if self.year is not None:
            doc[u'year'] = self.year

        if self.doi is not None:
            doc[u'doi'] = self.doi

        if self.inlinks is not None:
            doc[u'inlinks'] = self.inlinks

        if self.outlinks is not None:
            doc[u'outlinks'] = self.outlinks

        if self.id is not None:
            doc[u'id'] = self.id

        return doc

class Author():
    def __init__(self, lastname, firstname, doc_count=0, affiliation=None, email=None, id=None):
        self.lastname = lastname
        self.firstname = firstname
        self.doc_count = doc_count
        self.affiliation = affiliation
        self.email = email
        self.id = id

    @staticmethod
    def from_ref(ref):
        source = ref.to_dict()
        author = Author(source[u'lastname'], source[u'firstname'], source[u'doc_count'], id=ref.id)

        if u'affiliation' in source:
            author.affiliation = source[u'affiliation']

        if u'email' in source:
            author.email = source[u'email']

        return author

    def to_dict(self):
        author = {
            u'lastname': self.lastname,
            u'firstname': self.firstname,
            u'doc_count': self.doc_count,
        }

        if self.affiliation:
            author[u'affiliation'] = self.affiliation

        if self.email:
            author[u'email'] = self.email

        if self.id is not None:
            author[u'id'] = self.id

        return author

class Note():
    valid_notetypes = ["notes", "selections", "ideas", \
                       "todos", "measures", "designs", \
                       "procedures", "results", "summaries",
                       "challenges", "RQs", "theories"]

    def __init__(self, ref_id, notetype, body, id=None, page=None):
        self.ref_id = ref_id
        self.notetype = notetype
        self.body = body
        self.id = id
        self.page = page
        if self.notetype not in Note.valid_notetypes:
            raise ValueError(u'{0} is not a valid notetype'.format(notetype))

    @staticmethod
    def from_ref(ref):
        source = ref.to_dict()
        note = Note(source[u'ref_id'], source[u'notetype'], source[u'body'], id=ref.id)
        if u'page' in source:
            note.page = source[u'page']
        return note

    def to_dict(self):
        note = {
            u'ref_id': self.ref_id,
            u'notetype': self.notetype,
            u'body': self.body,
        }

        if self.id is not None:
            note[u'id'] = self.id

        if self.page is not None:
            note[u'page'] = self.page

        return note
