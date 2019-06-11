class Paper():
    def __init__(self, title=None, authors=None, year=None, doi=None, cited_by=[], citing=[], id=None):
        self.title = title
        self.authors = authors
        self.year = year
        if self.year is not None:
            self.year = int(year)
        self.doi = doi
        if self.doi is not None:
            self.doi = doi.lower()
        self.cited_by = cited_by
        self.citing = citing
        self.id = id

    @staticmethod
    def from_ref(ref):
        source = ref.to_dict()
        paper = Paper(title=source[u'title'], authors=source[u'authors'], id=ref.id)

        if u'year' in source:
            paper.year = source[u'year']

        if u'doi' in source:
            paper.doi = source[u'doi']

        if u'cited_by' in source:
            paper.cited_by = source[u'cited_by']

        if u'citing' in source:
            paper.citing = source[u'citing']

        return paper

    def to_dict(self):
        paper = {
            u'title': self.title,
            u'authors': self.authors,
        }

        if self.year is not None:
            paper[u'year'] = self.year

        if self.doi is not None:
            paper[u'doi'] = self.doi

        if self.cited_by is not None:
            paper[u'cited_by'] = self.cited_by

        if self.citing is not None:
            paper[u'citing'] = self.citing

        if self.id is not None:
            paper[u'id'] = self.id

        return paper

class Author():
    def __init__(self, lastname, firstname, paper_count=0, affiliation=None, email=None, id=None):
        self.lastname = lastname
        self.firstname = firstname
        self.paper_count = paper_count
        self.affiliation = affiliation
        self.email = email
        self.id = id

    @staticmethod
    def from_ref(ref):
        source = ref.to_dict()
        author = Author(source[u'lastname'], source[u'firstname'], source[u'paper_count'], id=ref.id)

        if u'affiliation' in source:
            author.affiliation = source[u'affiliation']

        if u'email' in source:
            author.email = source[u'email']

        return author

    def to_dict(self):
        author = {
            u'lastname': self.lastname,
            u'firstname': self.firstname,
            u'paper_count': self.paper_count,
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
