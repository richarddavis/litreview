import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1 import ArrayRemove, ArrayUnion
import google.cloud.exceptions
from document_types import *

class DatabaseDocMixin():
    def __init__(self):
        pass

    def add_doc(self, doc):
        doc_obj = self._get_doc_by_title(doc.title)
        if doc_obj is not None:
            print("Doc already in database.")
        else:
            print("Adding doc to database.")
            for author in doc.authors:
                new_author = Author(**author)
                self._add_author(new_author)
                author_snapshot = self._get_author(new_author)
                self._inc_author_doc_count(author_snapshot)
            self._get_docs().add(doc.to_dict())

    def _get_docs(self):
        return self.db.collection(u'docs')

    def _get_doc(self, doc):
        # This function checks the database for a doc with the same id.
        # If the doc hasn't been added, its ID is None.
        try:
            docs = self._get_docs()
            p = docs.document(doc.id)
            return p
        except google.cloud.exceptions.NotFound:
            return None

    def _get_doc_by_title(self, title):
        docs = self._get_docs()
        for p in docs.stream():
            if p.to_dict()[u'title'].lower() == title.lower():
                return Doc.from_ref(p)
        return None

    def get_doc(self, doc):
        try:
            p = self._get_docs().document(doc.id)
            return Doc.from_ref(p)
        except google.cloud.exceptions.NotFound:
            return None

    def get_docs(self):
        docs = self._get_docs()
        return [Doc.from_ref(p) for p in docs.stream()]

    def delete_doc(self, doc):
        doc_ref = self._get_doc(doc)
        if doc_ref is None:
            return False

        # Delete all attached notes
        note_snapshots = doc_ref.collection(u'notes').get()
        for note_snapshot in note_snapshots:
            note_snapshot.reference.delete()

        for author in doc.authors:
            new_author = Author(**author)
            author_snapshot = self._get_author(new_author)
            self._dec_author_doc_count(author_snapshot)

        doc_ref.delete()
        return True

    def add_link(self, out_doc, in_doc):
        # out_doc -> in_doc

        # out_doc.out_refs is updated with in_doc.ref
        # in_doc.in_refs is updated with out_doc.ref

        out_ref = self._get_doc(out_doc)
        in_ref = self._get_doc(in_doc)

        if out_ref is None or in_ref is None:
            print("No doc selected. Quitting.")
            return

        # Update out_doc.out_refs with in_doc.ref
        try:
            out_refs = out_ref.get().get(u'outlinks')
            out_refs.append(str(in_ref.id))
            out_ref.update({u'outlinks':out_refs})
        except KeyError:
            out_refs = [str(in_ref.id)]
            out_ref.update({u'outlinks':out_refs})

        # Update in_doc.in_refs with out_doc.ref
        try:
            in_refs = in_ref.get().get(u'inlinks')
            in_refs.append(str(out_ref.id))
            in_ref.update({u'inlinks':in_refs})
        except KeyError:
            in_refs = [str(out_ref.id)]
            in_ref.update({u'inlinks':in_refs})

    def delete_link(self, out_doc, in_doc):
        # When a doc is deleted any links that point to that doc should
        # also be removed. However, the program doesn't display these dangling
        # references to the user, so for now I'm not worrying about it.

        out_ref = self._get_doc(out_doc)
        in_ref = self._get_doc(in_doc)

        if out_ref is None or in_ref is None:
            print("No doc selected. Quitting.")
            return

        # Update out_doc.out_refs with in_doc.ref
        try:
            out_refs = out_ref.get().get(u'outlinks')
            print(out_refs)
            print(str(in_ref.id))
            out_refs.remove(str(in_ref.id))
            out_ref.update({u'outlinks':out_refs})
            return True
        except KeyError:
            return False

        # Update in_doc.in_refs with out_doc.ref
        try:
            in_refs = in_ref.get().get(u'inlinks')
            in_refs.remove(str(out_ref.id))
            in_ref.update({u'inlinks':in_refs})
            return True
        except KeyError:
            return False

    def add_note(self, note, doc):
        doc_ref = self._get_doc(doc)
        if doc_ref is None:
            print("Please add current doc to database before adding notes.")
            return

        note_refs = doc_ref.collection(u'notes')
        note_refs.add(note.to_dict())

    def get_notes(self, doc):
        doc_ref = self._get_doc(doc)
        if doc_ref is None:
            print("Please add current doc to database first.")
            return

        note_refs = doc_ref.collection(u'notes').get()
        return [Note.from_ref(note) for note in note_refs]

    def delete_note(self, note, doc):
        doc_ref = self._get_doc(doc)
        if doc_ref is None:
            return False
        note_snapshots = doc_ref.collection(u'notes').get()
        success = False
        for note_snapshot in note_snapshots:
            if note_snapshot.id == note.id:
                note_snapshot.reference.delete()
                success = True
                break
        if success == False:
            return success

        # Find any notes that referred to the note that was deleted and
        # reattach their reference to the doc.
        note_snapshots = doc_ref.collection(u'notes').get()
        for note_snapshot in note_snapshots:
            if note_snapshot.to_dict()[u'ref_id'] == note.id:
                note_snapshot.reference.update({u'ref_id':doc_ref.id})
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

    def _inc_author_doc_count(self, author_snapshot):
        count = author_snapshot.get(u'doc_count')
        new_count = int(count) + 1
        author_snapshot.reference.update({u'doc_count': str(new_count)})

    def _dec_author_doc_count(self, author_snapshot):
        count = author_snapshot.get(u'doc_count')
        if int(count) == 1:
            self._delete_author(author_snapshot.reference)
        else:
            new_count = int(count) - 1
            author_snapshot.reference.update({u'doc_count': str(new_count)})

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

class Database(DatabaseAuthorMixin, DatabaseDocMixin):
    def __init__(self):
        firebase_admin.initialize_app()
        self.db = firestore.client()
