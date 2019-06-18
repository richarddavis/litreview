from database import Database
from document_types import *

class Model():
    def __init__(self):
        self.db = Database()

        self.all_doc_ids = []
        self.doc_id_to_obj = {}

        self.all_note_ids = []
        self.note_id_to_obj = {}

        self.current_doc_id = None
        self.current_note_id = None

        self.history = []

        self.reload_docs()

    def set_current_obj(self, obj=None):
        if obj is None:
            print("Error. Nothing specified to set as current object.")
            return None

        if type(obj) is Doc:
            current_doc = self.doc_id_to_obj.get(obj.id)
            if current_doc is None:
                print("Error. Doc id unkonwn.")
                return None
            else:
                self.current_doc_id = obj.id
                self.reload_notes()
                self.history_push(obj)
                self.clear_current_note()
                return self.get_current_doc()
        elif type(obj) is Note:
            current_note = self.note_id_to_obj.get(obj.id)
            if current_note is None:
                print("Error. Note id unknown.")
                return None
            else:
                self.current_note_id = obj.id
                self.history_push(obj)
                return self.get_current_note()

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
        if self.current_doc_id is None:
            return None
        return self.doc_id_to_obj.get(self.current_doc_id)

    def add_doc(self, doc_obj):
        self.db.add_doc(doc_obj)
        self.reload_docs()

    def delete_doc(self, doc_obj):
        if doc_obj is not None:
            if doc_obj.id in self.all_doc_ids:
                self.db.delete_doc(doc_obj)
                self.history_delete_obj(doc_obj)
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
        if self.current_note_id is None:
            return None
        return self.note_id_to_obj.get(self.current_note_id)

    def clear_current_note(self):
        self.current_note_id = None

    def add_note(self, note_obj, doc_obj):
        self.db.add_note(note_obj, doc_obj)
        self.reload_docs()
        self.reload_notes()

    def delete_note(self, note_obj, doc_obj):
        self.db.delete_note(note_ob, doc_obj)
        self.history_delete_obj(note_obj)
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

    def history_push(self, obj):
        if getattr(obj, "id", None) is None:
            return None
        self.history.append(obj.id)

    def history_pop(self):
        try:
            obj_id = self.history.pop()
        except IndexError:
            return None

        if obj_id in self.all_doc_ids:
            return self.doc_id_to_obj.get(obj_id)
        elif obj_id in self.all_note_ids:
            return self.note_id_to_obj.get(obj_id)
        else:
            return None

    def history_delete_obj(self, obj):
        new_history = []
        for id in history:
            if obj.id == id:
                continue
            else:
                new_history.append(id)
        self.history = new_history

    def history_head(self):
        if not self.history:
            return None

        obj_id = self.history[-1]
        if obj_id in self.all_doc_ids:
            return self.doc_id_to_obj.get(obj_id)
        elif obj_id in self.all_note_ids:
            return self.note_id_to_obj.get(obj_id)
        else:
            return None

    def history_reset(self):
        self.history = []

    def history_back(self):
        cur_obj = self.history_pop()
        if cur_obj is None:
            return None

        prev_obj = self.history_pop()
        if prev_obj is None:
            self.set_current_obj(cur_obj)
            return None

        self.set_current_obj(prev_obj)
        return prev_obj

    def history_get(self):
        return self.history
