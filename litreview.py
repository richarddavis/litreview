import datetime
from time import sleep
from database import Database
from document_types import *
import cmd2
import textwrap

class LitreviewShell(cmd2.Cmd):
    def __init__(self):
        shortcuts = dict(self.DEFAULT_SHORTCUTS)
        shortcuts.update({'&': 'speak'})
        # Set use_ipython to True to enable the "ipy" command which embeds and interactive IPython shell
        super().__init__(use_ipython=False, multiline_commands=['orate'], shortcuts=shortcuts)

        self.INDENT = 5
        self.intro = u'\nWelcome to the Literature Review Shell. Type help or ? to list commands.\n'
        self.prompt = u'(lr) '
        self.db = Database()
        self.current_doc = None
        self.notes_at_current_level = []
        self.note_index_at_current_level = 0
        self.note_history = []
        self.cite_history = []
        self.all_docs = self.db.get_docs()

    def reset(self):
        self.prompt = u'(lr) '
        self.current_doc = None
        self.notes_at_current_level = []
        self.note_index_at_current_level = 0
        self.note_history = []

    def update_prompt(self):
        if self.current_doc is None:
            return
        truncated_title = self.current_doc.title[:40]
        self.prompt = u'(lr: ' + truncated_title + u'...) '

    def reload_docs(self):
        self.all_docs = self.db.get_docs()

    def print_indented(self, formatted_text, indentation_multiplier = 1):
        print(textwrap.fill(formatted_text,
                            initial_indent = " " * self.INDENT * indentation_multiplier,
                            subsequent_indent  = " " * self.INDENT * indentation_multiplier,
                            width = 80))

    def get_current_note(self):
        if self.note_history == []:
            return None
        else:
            return self.note_history[-1]

    def do_add_doc(self, line):
        print("")
        doc_dict = {}

        doctype_string = u'Select Doctype: \n'
        doctype_index = 0
        for doctype in Doc.valid_doctypes:
            doctype_string += u'    {0}: {1}\n'.format(doctype_index, doctype)
            doctype_index += 1

        try:
            doctype_index = input(doctype_string)
        except EOFError:
            return
        while not(doctype_index.isnumeric() and int(doctype_index) >= 0 and int(doctype_index) < len(Doc.valid_doctypes)):
            try:
                if input("That doctype does not exist. Try again? Y/n: ").lower() == u'y':
                    doctype_index = input(doctype_string)
                else:
                    print("Canceling add doc.")
                    print("")
                    return
            except EOFError:
                return

        try:
            doc_dict[u'title'] = input('Doc title: ')
        except EOFError:
            return

        print("")
        doc_dict[u'authors'] = []
        try:
            while input('Add author? Y/n: ').lower() == u'y':
                lastname = input('Author Last Name: ')
                firstname = input('Author First Name: ')
                doc_dict[u'authors'].append({u'lastname':lastname, u'firstname':firstname})
                print("")
        except EOFError:
            return

        print("")
        try:
            year = input('Year: ')
        except EOFError:
            return
        if year is not None:
            doc_dict[u'year'] = year
            print("")

        try:
            doi = input('DOI: ')
        except EOFError:
            return
        if doi is not "":
            doc_dict[u'doi'] = doi
            print("")

        doc = Doc(**doc_dict)
        self.db.add_doc(doc)
        self.all_docs = self.db.get_docs()

    def do_delete_doc(self, line):
        print("")
        if line == "" and self.current_doc is not None:
            # Delete self.current_doc
            self.print_indented("Selected doc: {0}".format(self.current_doc.title))
            try:
                if input("Delete this doc? Y/n: ").lower() == u'y':
                    deleted = self.db.delete_doc(self.current_doc)
                    if deleted == True:
                        self.reset()
                        self.reload_docs()
                        print("")
                        print("Doc deleted.")
                        print("")
                        return
                    else:
                        print("")
                        print("Error: Doc not deleted.")
                        print("")
                        return
            except EOFError:
                return
        else:
            while not (line != "" and line.isnumeric() and int(line) < len(self.all_docs) and int(line) >= 0):
                print("")
                doc_index = 0
                for doc in self.all_docs:
                    self.print_indented("[{0}]: {1}".format(doc_index, doc.title))
                    doc_index += 1
                    print("")
                try:
                    line = input('Please select a doc: ')
                except EOFError:
                    return

            self.print_indented("Selected doc: {0}".format(self.all_docs[int(line)].title))
            try:
                if input("Delete this doc? Y/n: ").lower() == u'y':
                    deleted = self.db.delete_doc(self.all_docs[int(line)])
                    if deleted == True:
                        self.reset()
                        self.reload_docs()
                        print("")
                        print("Doc deleted.")
                        print("")
                        return
                    else:
                        print("")
                        print("Doc deletion canceled.")
                        print("")
                        return
            except EOFError:
                return

    def do_docs(self, line):
        doc_index = 0
        for doc in self.all_docs:
            self.do_doc_info(str(doc_index))
            doc_index += 1

    def do_select_doc(self, line):
        while not (line != "" and line.isnumeric() and int(line) < len(self.all_docs) and int(line) >= 0):
            print("")
            doc_index = 0
            for doc in self.all_docs:
                self.print_indented("[{0}]: {1}".format(doc_index, doc.title))
                doc_index += 1
                print("")
            try:
                line = input('Please select a doc: ')
            except EOFError:
                return

        self.reset()
        self.current_doc = self.all_docs[int(line)]
        self.update_prompt()
        self.notes_at_current_level = self.get_notes_at_current_level(self.current_doc)
        self.do_note_tree("")

    def do_doc_info(self, line):
        print("")
        doc = None
        if line != "" and line.isnumeric():
            if int(line) >= len(self.all_docs) or int(line) < 0:
                print("That doc does not exist.")
                print("")
                return
            else:
                doc = self.all_docs[int(line)]
                self.print_indented("[{}]".format(line))
        else:
            if self.current_doc == None:
                print("Please select a doc first.")
                print("")
                return
            else:
                doc = self.current_doc
        self.print_indented("Title: {0}".format(doc.title))
        self.print_indented("Authors:")
        for author in doc.authors:
            self.print_indented("{0}, {1}".format(author[u'lastname'], author[u'firstname']), 2)
        self.print_indented("DOI: {0}".format(doc.doi))
        self.print_indented("Year: {0}".format(doc.year))
        self.print_indented("Number of notes: {0}".format(len(self.db.get_notes(doc))))
        print("")

    def do_add_cite(self, line):
        print("")
        line = ""
        doc_index = 0
        while not (line != "" and line.isnumeric() and int(line) < len(self.all_docs) and int(line) >= 0):
            for doc in self.all_docs:
                self.print_indented("[{0}]: {1}".format(doc_index, doc.title))
                doc_index += 1
                print("")
            try:
                line = input('Please select the CITING doc: ')
            except EOFError:
                return
        citing_doc = self.all_docs[int(line)]

        print("")
        line = ""
        doc_index = 0
        while not (line != "" and line.isnumeric() and int(line) < len(self.all_docs) and int(line) >= 0):
            for doc in self.all_docs:
                self.print_indented("[{0}]: {1}".format(doc_index, doc.title))
                doc_index += 1
                print("")
            try:
                line = input('Please select the CITED doc: ')
            except EOFError:
                return
        cited_doc = self.all_docs[int(line)]

        self.db.add_citation(citing_doc, cited_doc)

    def do_cites(self, line):
        if self.current_doc is None:
            print("")
            print("Please select a doc first.")
            print("")
            return
        citing = self.current_doc.citing
        self.print_indented("Citing:")
        index_map = {}
        current_index = 0
        for citing_doc_id in citing:
            master_index = 0
            for doc in self.all_docs:
                if citing_doc_id == doc.id:
                    self.print_indented("[{0}]: {1}".format(current_index, doc.title), 2)
                    index_map[current_index] = master_index
                    print("")
                master_index += 1
            current_index += 1

        cited_by = self.current_doc.cited_by
        self.print_indented("Cited by:")
        for cited_by_id in cited_by:
            master_index = 0
            for doc in self.all_docs:
                if cited_by_id == doc.id:
                    self.print_indented("[{0}]: {1}".format(current_index, doc.title), 2)
                    index_map[current_index] = master_index
                    print("")
                master_index += 1
            current_index += 1

        try:
            line = input('Jump to doc: ')
        except EOFError:
            return

        if not (line != "" and line.isnumeric() and int(line) < len(index_map) and int(line) >= 0):
            return

        self.cite_history.append(self.current_doc)
        self.reset()
        self.current_doc = self.all_docs[index_map[int(line)]]
        self.update_prompt()
        self.notes_at_current_level = self.get_notes_at_current_level(self.current_doc)
        self.do_note_tree("")

    def do_pop_cite(self, line):
        if self.cite_history == []:
            print("")
            print("Already at beginning.")
            print("")
            return
        self.reset()
        self.current_doc = self.cite_history.pop()
        self.update_prompt()
        self.notes_at_current_level = self.get_notes_at_current_level(self.current_doc)
        self.do_note_tree("")

    def get_notetypes_by_obj(self, target_obj):
        if self.current_doc is None:
            print("")
            print("Please select a doc first.")
            print("")
            return
        all_notes = self.db.get_notes(self.current_doc)
        return list({note.notetype for note in all_notes if note.ref_id == target_obj.id})

    def get_notes_by_obj(self, target_obj):
        if self.current_doc is None:
            print("")
            print("Please select a doc first.")
            print("")
            return
        all_notes = self.db.get_notes(self.current_doc)
        return [note for note in all_notes if note.ref_id == target_obj.id]

    def do_add_note(self, line):
        print("")
        note_dict = {}
        if self.current_doc == None:
            print("Pleast select a doc first.")
            print("")
            return

        target_obj = None
        if self.note_history == []:
            target_obj = self.current_doc
        else:
            target_obj = self.note_history[-1]

        note_dict[u'ref_id'] = target_obj.id

        notetype_string = u'Select Notetype: \n'
        notetype_index = 0
        for notetype in Note.valid_notetypes:
            notetype_string += u'    {0}: {1}\n'.format(notetype_index, notetype)
            notetype_index += 1

        try:
            notetype_index = input(notetype_string)
        except EOFError:
            return
        while not(notetype_index.isnumeric() and int(notetype_index) >= 0 and int(notetype_index) < len(Note.valid_notetypes)):
            try:
                if input("That notetype does not exist. Try again? Y/n: ").lower() == u'y':
                    notetype_index = input(notetype_string)
                else:
                    print("Canceling add note.")
                    print("")
                    return
            except EOFError:
                return

        print("")
        note_dict[u'notetype'] = Note.valid_notetypes[int(notetype_index)]
        try:
            note_dict[u'body'] = input("Note body: ")
        except EOFError:
            return

        print("")
        try:
            page = input("Page number: ").lower()
        except EOFError:
            return
        if page.isnumeric():
            note_dict[u'page'] = page

        note = Note(**note_dict)
        self.db.add_note(note, self.current_doc)
        self.notes_at_current_level = self.get_notes_at_current_level(target_obj)

    def do_delete_note(self, line):
        print("")
        if line == "" and self.get_current_note() is not None:
            current_note = self.get_current_note()
            self.print_indented("Selected note: {0}".format(current_note.body))
            try:
                if input("Delete this note? Y/n: ").lower() == u'y':
                    note_to_delete = current_note
                    deleted = self.db.delete_note(note_to_delete, self.current_doc)
                    if deleted == True:
                        try:
                            self.note_history.remove(note_to_delete)
                        except ValueError:
                            pass

                        if self.note_history == []:
                            self.notes_at_current_level = self.get_notes_at_current_level(self.current_doc)
                        else:
                            self.notes_at_current_level = self.get_notes_at_current_level(self.get_current_note())

                        print("")
                        print ("Note deleted.")
                        print("")
                        return
                    else:
                        print ("Error: Note not deleted.")
                else:
                    print("")
                    print("Cancelled note deletion.")
                    print("")
                    return
            except EOFError:
                return
        else:
            while not (line != "" and line.isnumeric() and int(line) < len(self.notes_at_current_level) and int(line) >= 0):
                print("")
                note_index = 0
                for note in self.notes_at_current_level:
                    self.print_indented("[{0}]: {1}".format(note_index, note.body))
                    note_index += 1
                    print("")
                try:
                    line = input('Please select a note: ')
                except EOFError:
                    return

            self.print_indented("Selected note: {0}".format(self.notes_at_current_level[int(line)].body))
            try:
                if input("Delete this note? Y/n: ").lower() == u'y':
                    note_to_delete = self.notes_at_current_level[int(line)]
                    deleted = self.db.delete_note(note_to_delete, self.current_doc)
                    if deleted == True:

                        try:
                            self.note_history.remove(note_to_delete)
                        except ValueError:
                            pass

                        if self.note_history == []:
                            self.notes_at_current_level = self.get_notes_at_current_level(self.current_doc)
                        else:
                            self.notes_at_current_level = self.get_notes_at_current_level(self.get_current_note())

                        print("")
                        print("Note deleted.")
                        print("")
                        return
                    else:
                        print("Error: Note not deleted.")
                else:
                    print("")
                    print("Cancelled note deletion.")
                    print("")
                    return
            except EOFError:
                return

    def do_notes(self, line):
        print("")
        if self.current_doc == None:
            print("Please select a doc first.")
            print("")
            return

        if self.notes_at_current_level == []:
            print("No notes at current level.")
            print("")
            return

        note_index = 0
        for note in self.notes_at_current_level:
            self.print_indented("[Note {0}:]".format(note_index))
            self.note_info(note)
            note_index += 1
            print("")

    def do_select_note(self, line):
        while not (line != "" and line.isnumeric() and int(line) < len(self.notes_at_current_level) and int(line) >= 0):
            self.do_notes("")
            try:
                line = input('Please select a note: ')
            except EOFError:
                return

        self.note_history.append(self.notes_at_current_level[int(line)])
        self.notes_at_current_level = self.get_notes_at_current_level(self.get_current_note())
        self.do_notes("")

    def do_pop_note(self, line):
        if self.note_history == []:
            print("")
            print("Already at top level.")
            print("")
            return

        self.note_history.pop()

        if self.note_history == []:
            self.notes_at_current_level = self.get_notes_at_current_level(self.current_doc)
        else:
            self.notes_at_current_level = self.get_notes_at_current_level(self.get_current_note())

        self.do_notes("")

    def get_notes_at_current_level(self, target_obj):
        if self.current_doc is None:
            print("")
            print("Please select a doc first.")
            print("")
            return
        all_notes = self.db.get_notes(self.current_doc)
        notes_at_current_level = []
        for note in all_notes:
            if note.ref_id == target_obj.id:
                notes_at_current_level.append(note)
        self.note_index_at_current_level = 0
        return notes_at_current_level

    def note_info(self, current_note, indentation_multiplier=1):
        if current_note is None:
            print("")
            print("No current note.")
            print("")
            return
        self.print_indented("Notetype: {0}".format(current_note.notetype), indentation_multiplier)
        self.print_indented("Body: {0}".format(current_note.body), indentation_multiplier)
        self.print_indented("Attached notetypes:", indentation_multiplier)
        notetypes = self.get_notetypes_by_obj(current_note)
        for notetype in notetypes:
            self.print_indented(notetype, indentation_multiplier + 1)

    def do_note_info(self, line):
        print("")
        cn = None
        if self.notes_at_current_level == []:
            print("No notes to show.")
            print("")
            return
        elif line == "":
            if self.get_current_note() is None:
                print("No current note.")
                print("")
                return
            cn = self.get_current_note()
        elif int(line) >= len(self.notes_at_current_level) or int(line) < 0:
            print("That note does not exist.")
            print("")
            return
        else:
            cn = self.notes_at_current_level[int(line)]

        self.print_indented("Notetype: {0}".format(cn.notetype))
        self.print_indented("Body: {0}".format(cn.body))
        self.print_indented("Attached notetypes:")
        notetypes = self.get_notetypes_by_obj(cn)
        for notetype in notetypes:
            self.print_indented(notetype, 2)
        print("")

    def do_get_next_note(self, line):
        print("")
        if self.notes_at_current_level == []:
            print("No notes at current level.")
            print("")
            return
        elif self.note_index_at_current_level >= len(self.notes_at_current_level):
            print("Returning to the first note at the current level.")
            print("")
            self.note_index_at_current_level = 0

        note = self.notes_at_current_level[self.note_index_at_current_level]

        self.print_indented("Notetype: {0}".format(note.notetype))
        self.print_indented("Body: {0}".format(note.body))
        self.print_indented("Attached notetypes:")
        notetypes = self.get_notetypes_by_obj(note)
        for notetype in notetypes:
            self.print_indented(notetype, 2)
        self.note_index_at_current_level += 1
        print("")

    def do_note_tree(self, line):
        depth = 1
        root_node = self.current_doc
        if root_node is None:
            print("")
            print("No doc selected.")
            print("")
            return
        if self.current_doc.id is None:
            print("")
            print("Currently selected doc has no id.")
            print("")
            return

        # note_list = self.db.get_all_notes_by_obj(self.current_doc)
        note_list = self.get_notes_by_obj(self.current_doc)
        if note_list == []:
            print("")
            print("No notes to show.")
            print("")
            return
        note_index = 0
        for note in note_list:
            self.note_tree_helper(note, depth, note_index)
            note_index += 1
            print("")

    def note_tree_helper(self, current_note, depth, note_index):
        print("")
        self.print_indented("[Note {0}:]".format(note_index), depth)
        self.note_info(current_note, depth)
        note_list = self.get_notes_by_obj(current_note)
        if note_list == []:
            return
        else:
            child_note_index = 0
            for note in note_list:
                self.note_tree_helper(note, depth+1, child_note_index)
                child_note_index += 1

    def do_EOF(self, line):
        return True

    def postloop(self):
        print

if __name__ == '__main__':
    try:
        LitreviewShell().cmdloop()
    except KeyboardInterrupt:
        print("^C")
