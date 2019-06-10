class Paper():
    def __init__(self, title, doi, authors, year, id=None):
        self.title = title
        self.doi = doi.lower()
        self.authors = authors
        self.year = int(year)
        self.id = id

    @staticmethod
    def from_ref(ref):
        source = ref.to_dict()
        paper = Paper(source[u'title'], source[u'doi'], source[u'authors'], \
                      source[u'year'], ref.id)
        return paper

    def to_dict(self):
        paper = {
            u'title': self.title,
            u'doi': self.doi,
            u'authors': self.authors,
            u'year': self.year,
        }

        if self.id is not None:
            paper[u'id'] = self.id
        return paper

class Author():
    def __init__(self, lastname, firstname, affiliation=None, email=None, id=None):
        self.lastname = lastname
        self.firstname = firstname
        self.affiliation = affiliation
        self.email = email
        self.id = id

    @staticmethod
    def from_ref(ref):
        source = ref.to_dict()
        author = Author(source[u'lastname'], source[u'firstname'], ref.id)

        if u'affiliation' in source:
            author.affiliation = source[u'affiliation']

        if u'email' in source:
            author.email = source[u'email']

        return author

    def to_dict(self):
        author = {
            u'lastname': self.lastname,
            u'firstname': self.firstname,
        }

        if self.id is not None:
            author[u'id'] = self.id

        if self.affiliation:
            author[u'affiliation'] = self.affiliation

        if self.email:
            author[u'email'] = self.email

        return author

class Note():
    valid_notetypes = ["notes", "selections", "ideas", \
                       "todos", "measures", "designs", \
                       "procedures", "results", "summaries"]

    def __init__(self, ref_id, notetype, body, id=None):
        self.ref_id = ref_id
        self.notetype = notetype
        self.body = body
        self.id = id
        if self.notetype not in Note.valid_notetypes:
            raise ValueError(u'{0} is not a valid notetype'.format(notetype))

    @staticmethod
    def from_ref(ref):
        source = ref.to_dict()
        note = Note(source[u'ref_id'], source[u'notetype'], source[u'body'], ref.id)
        return note

    def to_dict(self):
        note = {
            u'ref_id': self.ref_id,
            u'notetype': self.notetype,
            u'body': self.body,
        }

        if self.id is not None:
            note[u'id'] = self.id

        return note
