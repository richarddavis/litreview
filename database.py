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
        paper_ref = self._get_paper_by_title(paper.title)
        if paper_ref is not None:
            print("Paper already in database.")
        else:
            print("Adding paper to database.")
            for author in paper.authors:
                new_author = Author(**author)
                self.add_author(new_author)
            self._get_papers().add(paper.to_dict())

    def _get_papers(self):
        return self.db.collection(u'papers')

    def _get_paper(self, paper):
        # This function checks the database for a paper with the same id.
        # If the paper hasn't been added, its ID is None.
        try:
            papers = self._get_papers()
            p = papers.document(paper.id)
            return p
        except google.cloud.exceptions.NotFound:
            return None

    def _get_paper_by_title(self, title):
        papers = self._get_papers().get()
        for p in papers:
            if p.to_dict()[u'title'].lower() == title.lower():
                return Paper.from_ref(p)
        return None

    def get_paper(self, paper):
        try:
            p = self._get_papers().document(paper.id)
            return Paper.from_ref(p)
        except google.cloud.exceptions.NotFound:
            return None

    def get_papers(self):
        papers = self._get_papers()
        return [Paper.from_ref(p) for p in papers.stream()]

    def add_note(self, note, paper):
        paper_ref = self._get_paper(paper)
        if paper_ref is None:
            print("Please add current paper to database before adding notes.")
            return

        notes_ref = paper_ref.collection(u'notes')
        notes_ref.add(note.to_dict())

    def get_notes(self, paper):
        paper_ref = self._get_paper(paper)
        if paper_ref is None:
            print("Please add current paper to database first.")
            return

        notes_ref = paper_ref.collection(u'notes').get()
        return [Note.from_ref(note) for note in notes_ref]

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

# class DatabaseNoteMixin():
#     def __init__(self):
#         pass

#     def add_note(self, note):
#         return self.db.collection(note.notetype).add(note.to_dict())

#     def _get_notes(self, notetype):
#         return self.db.collection(notetype)

#     def get_notes_by_obj(self, obj, notetype):
#         notes = self._get_notes(notetype).where(u'ref_id', u'==', obj.id).stream()
#         note_list = [Note.from_ref(note) for note in notes]
#         return note_list

#     def get_all_notes_by_obj(self, obj):
#         all_notes = []
#         for notetype in Note.valid_notetypes:
#             notes = self._get_notes(notetype).where(u'ref_id', u'==', obj.id).stream()
#             note_list = [Note.from_ref(note) for note in notes]
#             all_notes += note_list
#         return all_notes

class Database(DatabaseAuthorMixin, DatabasePaperMixin):
    def __init__(self):
        firebase_admin.initialize_app()
        self.db = firestore.client()
