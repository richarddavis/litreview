from database import Database
from document_types import *
from pubsub import pub

class Model():
    def __init__(self):
        self.db = Database()

        self.all_doc_ids = []
        self.doc_id_to_obj = {}

        self.all_note_ids = []
        self.note_id_to_obj = {}

        self.history = History(self)
        pub.subscribe(self._new_current_doc_listener, 'new_current_doc')
        pub.subscribe(self._new_current_note_listener, 'new_current_note')

        self.reload_docs()

    def set_current_obj(self, obj=None):
        if obj is None:
            print("Error. Nothing specified to set as current object.")
            return

        if type(obj) is Doc:
            current_doc = self.doc_id_to_obj.get(obj.id)
            if current_doc is None:
                print("Error. Doc id unkonwn.")
                return
            else:
                self.history.push_doc(obj.id)
                return
        elif type(obj) is Note:
            current_note = self.note_id_to_obj.get(obj.id)
            if current_note is None:
                print("Error. Note id unknown.")
                return
            else:
                self.history.push_note(obj.id)
                return

    def get_current_obj(self):
        current_obj_id = self.history.head()
        if current_obj_id is None:
            return None
        else:
            if current_obj_id in self.all_doc_ids:
                return self.doc_id_to_obj.get(current_obj_id)
            elif current_obj_id in self.all_note_ids:
                return self.note_id_to_obj.get(current_obj_id)
            else:
                return None

    def _new_current_doc_listener(self):
        self.reload_notes()
        self.clear_current_note()

    def _new_current_note_listener(self):
        pass

    def reset_docs(self):
        self.all_doc_ids = []
        self.doc_id_to_obj = {}

    def reset_notes(self):
        self.all_note_ids = []
        self.note_id_to_obj = {}

    def reload_docs(self):
        self.reset_docs()
        doc_objs = self.db.get_docs()
        doc_obj_index = 0
        for doc_obj in doc_objs:
            self.all_doc_ids.append(doc_obj.id)
            self.doc_id_to_obj[doc_obj.id] = doc_obj
            doc_obj_index += 1

    def get_current_doc(self):
        current_doc_id = self.history.get_current_doc_id()
        if current_doc_id is None:
            return None
        return self.doc_id_to_obj.get(current_doc_id)

    def add_doc(self, doc_obj):
        self.db.add_doc(doc_obj)
        self.reload_docs()

    def delete_doc(self, doc_obj):
        if doc_obj is not None:
            if doc_obj.id in self.all_doc_ids:
                self.db.delete_doc(doc_obj)
                self.history.delete_doc(doc_obj.id)
                self.reload_docs()
                return True
        return False

    def get_docs(self):
        return [self.doc_id_to_obj.get(id) for id in self.all_doc_ids]

    def get_doc(self, id):
        return self.doc_id_to_obj.get(id)

    def reload_notes(self):
        current_doc = self.get_current_doc()
        if current_doc is None:
            return
        self.reset_notes()
        note_objs = self.db.get_notes(current_doc)
        note_obj_index = 0
        for note_obj in note_objs:
            self.all_note_ids.append(note_obj.id)
            self.note_id_to_obj[note_obj.id] = note_obj
            note_obj_index += 1

    def get_current_note(self):
        current_note_id = self.history.get_current_note_id()
        if current_note_id is None:
            return None
        return self.note_id_to_obj.get(current_note_id)

    def clear_current_note(self):
        self.current_note_id = None

    def add_note(self, note_obj, doc_obj):
        self.db.add_note(note_obj, doc_obj)
        self.reload_docs()
        self.reload_notes()

    def delete_note(self, note_obj, doc_obj):
        self.db.delete_note(note_ob, doc_obj)
        self.history.delete_note(note_obj.id)
        self.reload_docs()
        self.reload_notes()

    def get_notes(self, target_obj=None):
        return [self.note_id_to_obj.get(id) for id in self.all_note_ids]

    def get_note(self, id):
        return self.note_id_to_obj.get(id)

    def create_link(self, out_obj, in_obj):
        self.db.add_link(out_obj, in_obj)
        self.reload_docs()
        self.reload_notes()

    def delete_link(self, out_obj, in_obj):
        if self.db.delete_link(out_obj, in_obj) == True:
            self.reload_docs()
            self.reload_notes()
            return True
        else:
            return False

class History():
    # self.note_history is a list of lists.
    # Pushing a doc adds a new entry to self.doc_history and a new list to self.note_history.
    # Pushing a note does not affect self.doc_history and adds a new note id to self.note_history[-1].

    def __str__(self):
        return_string = ""
        for doc_id, note_ids in zip(self.doc_history, self.note_history):
            return_string += "Doc ID: " + doc_id + "\n"
            return_string += "Note IDs: "
            for note_id in note_ids:
                return_string += note_id + ", "
            return_string += "\n"
        return return_string

    def __init__(self, model):
        self.model = model
        self.doc_history = []
        self.note_history = []

    def get_current_doc_id(self):
        try:
            return self.doc_history[-1]
        except IndexError:
            return None

    def get_current_note_id(self):
        try:
            return self.note_history[-1][-1]
        except IndexError:
            return None

    def head(self):
        try:
            return self.note_history[-1][-1]
        except IndexError:
            try:
                return self.doc_history[-1]
            except IndexError:
                return None

    def reset(self):
        self.doc_history = []
        self.note_history = []

    def push_doc(self, doc_id):
        self.doc_history.append(doc_id)
        self.note_history.append([])
        pub.sendMessage('new_current_doc')

    def push_note(self, note_id):
        self.note_history[-1].append(note_id)
        pub.sendMessage('new_current_note')

    def pop(self):
        try:
            note_id = self.note_history[-1].pop()
            pub.sendMessage('new_current_note')
            return note_id
        except IndexError: # Attempted to pop() from an empty list...
            try:
                doc_id = self.doc_history.pop()
                self.note_history.pop()
                pub.sendMessage('new_current_doc')
                return doc_id
            except IndexError:
                return None

    def back(self):
        cur_obj = self.pop()
        if cur_obj is None:
            return None

        return self.head()

    def delete_doc(self, id):
        new_current_doc = False
        try:
            current_doc_id = self.doc_history[-1]
            if current_doc_id == id:
                new_current_doc = True
        except IndexError:
            return

        new_doc_history = []
        new_note_history = []
        for doc_id, note_ids in zip(self.doc_history, self.note_history):
            if id == doc_id:
                continue
            else:
                new_doc_history.append(doc_id)
                new_note_history.append(note_ids)

        if new_current_doc:
            pub.sendMessage('new_current_doc')

    def delete_note(self, id):
        new_current_note = False
        try:
            current_note_id = self.note_history[-1][-1]
            if current_note_id == id:
                new_current_note = True
        except IndexError:
            pass

        new_note_history = []
        for note_ids in self.note_history:
            new_note_history.append([])
            for note_id in note_ids:
                if id == note_id:
                     continue
                else:
                    new_note_history[-1].append(note_id)


        if new_current_note:
            pub.sendMessage('new_current_note')
