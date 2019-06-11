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
        paper_obj = self._get_paper_by_title(paper.title)
        if paper_obj is not None:
            print("Paper already in database.")
        else:
            print("Adding paper to database.")
            for author in paper.authors:
                new_author = Author(**author)
                self._add_author(new_author)
                author_snapshot = self._get_author(new_author)
                self._inc_author_paper_count(author_snapshot)
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
        papers = self._get_papers()
        for p in papers.stream():
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

    def delete_paper(self, paper):
        paper_ref = self._get_paper(paper)
        if paper_ref is not None:
            paper_ref.delete()
            for author in paper.authors:
                new_author = Author(**author)
                author_snapshot = self._get_author(new_author)
                self._dec_author_paper_count(author_snapshot)
            return True
        else:
            return False

    def add_citation(self, citing_paper, cited_paper):
        citing_paper_ref = self._get_paper(citing_paper)
        cited_paper_ref = self._get_paper(cited_paper)

        if citing_paper_ref is None or cited_paper_ref is None:
            print("No paper selected. Quitting.")
            return
        try:
            citing_papers_out_citations = citing_paper_ref.get().get(u'citing')
            citing_papers_out_citations.append(str(cited_paper_ref.id))
            citing_paper_ref.update({u'citing':citing_papers_out_citations})
        except KeyError:
            cited_papers = [str(cited_paper_ref.id)]
            citing_paper_ref.update({u'citing':cited_papers})

        try:
            cited_papers_in_citations = cited_paper_ref.get().get(u'cited_by')
            cited_papers_in_citations.append(str(citing_paper_ref.id))
            cited_paper_ref.update({u'cited_by':cited_papers_in_citations})
        except KeyError:
            citing_papers = [str(citing_paper_ref.id)]
            cited_paper_ref.update({u'cited_by':citing_papers})

    def delete_citation(self):
        # When a paper is deleted any citations that point to that paper should
        # also be deleted. However, the program doesn't display these dangling
        # references to the user, so for now I'm not worrying about it.
        pass

    def add_note(self, note, paper):
        paper_ref = self._get_paper(paper)
        if paper_ref is None:
            print("Please add current paper to database before adding notes.")
            return

        note_refs = paper_ref.collection(u'notes')
        note_refs.add(note.to_dict())

    def get_notes(self, paper):
        paper_ref = self._get_paper(paper)
        if paper_ref is None:
            print("Please add current paper to database first.")
            return

        note_refs = paper_ref.collection(u'notes').get()
        return [Note.from_ref(note) for note in note_refs]

    def delete_note(self, note, paper):
        paper_ref = self._get_paper(paper)
        if paper_ref is None:
            return False
        note_refs = paper_ref.collection(u'notes').get()
        success = False
        for note_ref in note_refs:
            if note_ref.to_dict()[u'id'] == note.id:
                note_ref.delete()
                success = True
                break
        if success == False:
            return success

        # Find any notes that referred to the note that was deleted and
        # reattach their reference to the paper.
        for note_ref in note_refs:
            if note_ref.to_dict()[u'ref_id'] == note.id:
                note_ref.update({u'ref_id':paper_ref.id})
        return success

class DatabaseAuthorMixin():
    def __init__(self):
        pass

    def _add_author(self, new_author):
        author_snapshot = self._get_author(new_author)
        if author_snapshot is not None:
            print("Author alredy in database.")
            return
        else:
            print("Adding author to database.")
            self._get_authors().add(new_author.to_dict())
            return

    def _get_authors(self):
        return self.db.collection(u'authors')

    def _get_author(self, author):
        # Search by last name and first name.
        authors = list(self._get_authors().where(u'lastname', u'==', author.lastname).where(u'firstname', u'==', author.firstname).stream())
        if len(authors) == 0:
            return None
        else:
            return authors[0]

    def _inc_author_paper_count(self, author_snapshot):
        count = author_snapshot.get(u'paper_count')
        new_count = int(count) + 1
        author_snapshot.reference.update({u'paper_count': str(new_count)})

    def _dec_author_paper_count(self, author_snapshot):
        count = author_snapshot.get(u'paper_count')
        if int(count) == 1:
            self._delete_author(author_snapshot.reference)
        else:
            new_count = int(count) - 1
            author_snapshot.reference.update({u'paper_count': str(new_count)})

    def _delete_author(self, author_ref):
        author_ref.delete()

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
