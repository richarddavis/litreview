import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1 import ArrayRemove, ArrayUnion
import google.cloud.exceptions
from document_types import *

class DatabasePaperMixin():
    def __init__(self):
        pass

    def add_paper(self, paper):
        paper_ref = self._get_paper(paper)
        if paper_ref is not None:
            print("Paper already in database.")
            # return Paper.from_ref(paper_ref)
        else:
            print("Adding paper to database.")
            for author in paper.authors:
                new_author = Author(**author)
                self.add_author(new_author)
            self._get_papers().add(paper.to_dict())
            # paper_ref = self._get_papers().add(paper.to_dict())[1]
            # return Paper.from_ref(paper_ref)

    def _get_papers(self):
        return self.db.collection(u'papers')

    def _get_paper(self, paper):
        # For now, only searching by doi.
        papers = list(self._get_papers().where(u'doi', u'==', paper.doi).stream())
        if len(papers) == 0:
            return None
        else:
            return papers[0]

    def get_paper_by_doi(self, doi):
        papers = list(self._get_papers().where(u'doi', u'==', doi).stream())
        if len(papers) == 0:
            return None
        else:
            return Paper.from_ref(papers[0])

    def get_papers(self):
        papers = self._get_papers()
        return [Paper.from_ref(p) for p in papers.stream()]

class DatabaseAuthorMixin():
    def __init__(self):
        pass

    def add_author(self, new_author):
        author_ref = self._get_author(new_author)
        if author_ref is not None:
            print("Author alredy in database.")
        else:
            print("Adding author to database.")
            self._get_authors().add(new_author.to_dict())

    def _get_authors(self):
        return self.db.collection(u'authors')

    def _get_author(self, author):
        # Search by last name and first name.
        authors = list(self._get_authors().where(u'lastname', u'==', author.lastname).where(u'firstname', u'==', author.firstname).stream())
        if len(authors) == 0:
            return None
        else:
            return authors[0]

class DatabaseNoteMixin():
    def __init__(self):
        pass

    def add_note(self, note):
        return self.db.collection(note.notetype).add(note.to_dict())

    def _get_notes(self, notetype):
        return self.db.collection(notetype)

    def get_notes_by_obj(self, obj, notetype):
        notes = self._get_notes(notetype).where(u'ref_id', u'==', obj.id).stream()
        note_list = [Note.from_ref(note) for note in notes if note.to_dict()['notetype'] == notetype]
        return note_list

    def get_notetypes_by_obj(self, obj):
        notetypes = []
        for notetype in Note.valid_notetypes:
            notes = self._get_notes(notetype).where(u'ref_id', u'==', obj.id).stream()
            if len(list(notes)) != 0:
                notetypes.append(notetype)
        return notetypes

class Database(DatabaseNoteMixin, DatabaseAuthorMixin, DatabasePaperMixin):
    def __init__(self):
        firebase_admin.initialize_app()
        self.db = firestore.client()
