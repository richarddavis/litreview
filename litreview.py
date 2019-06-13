from datetime import datetime
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
        self.current_doc_index = None
        self.child_notes = []
        self.child_note_index = 0
        self.note_history = []
        self.link_history = []
        self.all_docs = self.db.get_docs()
        self.all_notes = []

    def reset(self):
        self.prompt = u'(lr) '
        self.current_doc = None
        self.current_doc_index = None
        self.child_notes = []
        self.child_note_index = 0
        self.note_history = []
        self.all_notes = []

    def update_prompt(self):
        if self.current_doc is None:
            return
        truncated_title = self.current_doc.title[:40]
        self.prompt = u'(lr: ' + truncated_title + u'...) '

    def do_whereami(self, line):
        truncated = True
        if line != "":
            truncated = False

        if truncated == True:
            if self.current_doc is not None:
                self.print_indented("Current doc: {}...".format(self.current_doc.title[:40]))
            if self.get_current_note() is not None:
                self.print_indented("Current note: {}...".format(self.get_current_note().body[:40]))
        else:
            if self.current_doc is not None:
                self.print_indented("Current doc: {}".format(self.current_doc.title))
            if self.get_current_note() is not None:
                self.print_indented("Current note: {}".format(self.get_current_note().body))

    # PROBLEM: When self.reload_docs() or self.reload_notes() is called,
    # link_history and note_history will both be corrupted.
    # Keep in mind that self.all_docs and self.all_notes are sorted, so simply replacing them
    # with a dict that maps ids to objects would not work.
    # One solution could be to keep a dict mapping id to the index in all_notes or all_docs.
    # Then, note_history and link_history could store ids, and pushing to and popping from
    # history could be managed by a helper function that accepts and returns objects, but
    # works with ids and indices internally.

    def reload_docs(self):
        self.all_docs = self.db.get_docs()

    def reload_notes(self):
        if self.current_doc == None:
            return
        self.all_notes = self.db.get_notes(self.current_doc)

    def get_notes(self):
        return self.all_notes

    def set_current_doc(self, doc_obj=None):
        # if not args:
        #     doc_index = self.current_doc_index
        # else:
        #     doc_index = args[0]

        if doc_obj is None:
            print("Error. Unable to set current doc.")
            return

        if doc_obj in self.all_docs:
            self.current_doc = doc_obj
            self.reload_notes()
            return
        else:
            matching_docs = [d for d in self.all_docs if d.id == doc_obj.id]
            if len(matching_docs) > 0:
                self.current_doc = matching_docs[0]
                self.reload_notes()
                return
            else:
                print("Error. Unable to set current doc.")
                return

    def print_indented(self, formatted_text, indentation_multiplier = 1):
        print(textwrap.fill(formatted_text,
                            initial_indent = " " * self.INDENT * indentation_multiplier,
                            subsequent_indent  = " " * self.INDENT * indentation_multiplier,
                            width = 150))

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
        print("")

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
        self.set_current_doc(self.all_docs[int(line)])
        self.update_prompt()
        self.child_notes = self.get_child_notes(self.current_doc)
        self.do_note_tree("")

    def do_doc(self, line):
        if self.current_doc is None:
            return

        if line == "links":
            self.get_links(self.current_doc)
            return
        else:
            print("")
            self.print_doc_info(self.current_doc)
            print("")
            return

    def print_doc_info(self, doc):
        if doc is None:
            print ("No document selected.")
            return

        self.print_indented("Title: {0}".format(doc.title))
        self.print_indented("Authors:")
        for author in doc.authors:
            self.print_indented("{0}, {1}".format(author[u'lastname'], author[u'firstname']), 2)
        self.print_indented("DOI: {0}".format(doc.doi))
        self.print_indented("Year: {0}".format(doc.year))
        self.print_indented("Number of notes: {0}".format(len(self.db.get_notes(doc))))

    def do_doc_info(self, line):
        doc = None
        if line != "" and line.isnumeric():
            if int(line) >= len(self.all_docs) or int(line) < 0:
                print("")
                print("That doc does not exist.")
                print("")
                return
            else:
                doc = self.all_docs[int(line)]
                print("")
                self.print_indented("[{}]".format(line))
        else:
            if self.current_doc == None:
                print("")
                print("Please select a doc first.")
                print("")
                return
            else:
                doc = self.current_doc

        self.print_doc_info(doc)

    def do_link(self, line):
        if self.current_doc is None:
            print("")
            print("Please select a doc first.")
            print("")
            return

        link_from = "doc"
        link_to = "doc"

        commands = line.split()
        if len(commands) == 1:
            if commands[0] == "note":
                link_from = "note"
        elif len(commands) == 3:
            if commands[0] == "note":
                link_from = "note"
            if commands[2] == "note":
                link_to = "note"

        in_obj = None
        if link_to == "doc":
            print("")
            choice = ""
            doc_index = 0
            while not (choice != "" and choice.isnumeric() and int(choice) < len(self.all_docs) and int(choice) >= 0):
                for doc in self.all_docs:
                    self.print_indented("[{0}]: {1}".format(doc_index, doc.title))
                    doc_index += 1
                    print("")
                try:
                    choice = input('Please select the doc to link to: ')
                except EOFError:
                    return
            in_obj = self.all_docs[int(choice)]
        elif link_to == "note":
            pass

        if in_obj is None:
            return

        if link_from == "doc":
            self.db.add_link(self.current_doc, in_obj)
            self.reload_docs()
            self.set_current_doc(self.current_doc)
        elif link_from == "note":
            self.db.add_link(self.get_current_note(), in_obj)
            self.reload_notes()
            # PROBLEM: Reload notes is not refreshing the current_note.
            # See how set_current_doc works for a possible fix.

    def do_delete_link(self, line):
        if self.current_doc is None:
            print("")
            print("Please select a doc first.")
            print("")
            return

        outlinks = self.current_doc.outlinks
        self.print_indented("Outlinks:")
        index_map = {}
        current_index = 0
        for outlinks_doc_id in outlinks:
            master_index = 0
            for doc in self.all_docs:
                if outlinks_doc_id == doc.id:
                    self.print_indented("[{0}]: {1}".format(current_index, doc.title), 2)
                    index_map[current_index] = master_index
                    print("")
                master_index += 1
            current_index += 1

        try:
            line = input('Select link to delete: ')
        except EOFError:
            return

        if not (line != "" and line.isnumeric() and int(line) < len(index_map) and int(line) >= 0):
            return

        deleted = self.db.delete_link(self.current_doc, self.all_docs[index_map[int(line)]])
        if deleted == True:
            self.reload_docs()
            self.set_current_doc(self.current_doc)
            print("")
            print("Link deleted.")
            print("")
            return
        else:
            print("")
            print("Error: Link not deleted.")
            print("")
            return

    def get_links(self, obj=None):

        if obj is None:
            return

        outlinks = obj.outlinks
        index_map = {}
        current_index = 0
        print("")

        if len(outlinks) > 0:
            self.print_indented("Outlinks:")
            print("")
            for outlinks_doc_id in outlinks:
                master_index = 0
                for doc in self.all_docs:
                    if outlinks_doc_id == doc.id:
                        self.print_indented("[{0}]: {1}".format(current_index, doc.title), 2)
                        index_map[current_index] = master_index
                        print("")
                    master_index += 1
                current_index += 1

        inlinks = obj.inlinks
        if len(inlinks) > 0:
            self.print_indented("Inlinks:")
            for inlinks_id in inlinks:
                master_index = 0
                for doc in self.all_docs:
                    if inlinks_id == doc.id:
                        self.print_indented("[{0}]: {1}".format(current_index, doc.title), 2)
                        index_map[current_index] = master_index
                        print("")
                    master_index += 1
                current_index += 1
            print("")

        try:
            line = input('Jump to doc: ')
        except EOFError:
            return

        if not (line != "" and line.isnumeric() and int(line) < len(index_map) and int(line) >= 0):
            return

        self.link_history.append(obj)
        self.reset()
        self.set_current_doc(self.all_docs[index_map[int(line)]])
        self.update_prompt()
        self.child_notes = self.get_child_notes(obj)
        self.do_note_tree("")

    # PROBLEM: Since I've added the ability to link from notes, the pop functions may be broken.

    def do_pop(self, line):
        if line == "note":
            self.pop_note("")
        elif line == "doc":
            self.pop_link("")
        else:
            if self.note_history != []:
                self.pop_note("")
            elif self.link_history != []:
                self.pop_link("")
            else:
                print("")
                print("Nothing to pop.")
                print("")

    def pop_link(self, line):
        if self.link_history == []:
            print("")
            print("Already at beginning.")
            print("")
            return
        self.reset()
        new_current_doc = self.link_history.pop()
        self.set_current_doc(new_current_doc)
        self.update_prompt()
        self.child_notes = self.get_child_notes(self.current_doc)
        self.do_note_tree("")

    def get_notetypes_by_obj(self, target_obj):
        if self.current_doc is None:
            print("")
            print("Please select a doc first.")
            print("")
            return
        all_notes = self.get_notes()
        return list({note.notetype for note in all_notes if note.ref_id == target_obj.id})

    def get_notes_by_obj(self, target_obj):
        if self.current_doc is None:
            print("")
            print("Please select a doc first.")
            print("")
            return
        all_notes = self.get_notes()
        obj_notes = [note for note in all_notes if note.ref_id == target_obj.id]
        obj_notes.sort()
        return obj_notes

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
        self.reload_notes()
        self.child_notes = self.get_child_notes(target_obj)

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

                        self.reload_notes()
                        if self.note_history == []:
                            self.child_notes = self.get_child_notes(self.current_doc)
                        else:
                            self.child_notes = self.get_child_notes(self.get_current_note())

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
            while not (line != "" and line.isnumeric() and int(line) < len(self.child_notes) and int(line) >= 0):
                print("")
                note_index = 0
                for note in self.child_notes:
                    self.print_indented("[{0}]: {1}".format(note_index, note.body))
                    note_index += 1
                    print("")
                try:
                    line = input('Please select a note: ')
                except EOFError:
                    return

            self.print_indented("Selected note: {0}".format(self.child_notes[int(line)].body))
            try:
                if input("Delete this note? Y/n: ").lower() == u'y':
                    note_to_delete = self.child_notes[int(line)]
                    deleted = self.db.delete_note(note_to_delete, self.current_doc)
                    if deleted == True:

                        try:
                            self.note_history.remove(note_to_delete)
                        except ValueError:
                            pass

                        self.reload_notes()
                        if self.note_history == []:
                            self.child_notes = self.get_child_notes(self.current_doc)
                        else:
                            self.child_notes = self.get_child_notes(self.get_current_note())

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
        if self.current_doc == None:
            print("")
            print("Please select a doc first.")
            print("")
            return

        if self.child_notes == []:
            print("")
            print("No attached notes.")
            print("")
            return

        truncated = True
        if line != "":
            truncated = False

        note_index = 0
        print("")
        for note in self.child_notes:
            self.print_indented("[Note {0}:]".format(note_index))
            self.print_note_info(note, truncated=truncated)
            print("")
            note_index += 1

    def do_select_note(self, line):
        note_indices = line.split()
        if len(note_indices) == 0:
            self.do_notes("")
            try:
                line = input('Please select a note: ')
                note_indices = [line]
            except EOFError:
                return

        current_note_backup = self.get_current_note()
        child_notes_backup = self.child_notes

        for ni in note_indices:
            if not (ni.isnumeric() and int(ni) < len(self.child_notes) and int(ni) >= 0):
                self.child_notes = child_notes_backup
                print("")
                print("No note selected.")
                print("")
                return
            else:
                temp_note = self.child_notes[int(ni)]
                self.child_notes = self.get_child_notes(temp_note)
                # print("temp_note is {}".format(temp_note))
                # print("get_child_notes() returned {}".format(self.child_notes))

        self.note_history.append(temp_note)
        self.do_notes("")

    def pop_note(self, line):
        if self.note_history == []:
            print("")
            print("Already at top level.")
            print("")
            return

        self.note_history.pop()

        if self.note_history == []:
            self.child_notes = self.get_child_notes(self.current_doc)
        else:
            self.child_notes = self.get_child_notes(self.get_current_note())

        self.do_notes("")

    def get_child_notes(self, target_obj):
        if self.current_doc is None:
            print("")
            print("Please select a doc first.")
            print("")
            return
        all_notes = self.get_notes()
        child_notes = []
        for note in all_notes:
            if note.ref_id == target_obj.id:
                child_notes.append(note)

        child_notes.sort()
        self.child_note_index = 0
        return child_notes

    def print_note_info(self, note, indentation_multiplier=1, truncated=True, verbose=True):
        if note is None:
            print("No note selected.")
            return

        if verbose == True:
            self.print_indented("Notetype: {0}, Page: {1}".format(note.notetype, getattr(note, 'page', 'NA')), indentation_multiplier)
            if truncated == False:
                self.print_indented("Body: {0}".format(note.body), indentation_multiplier)
                self.print_indented("Attached notetypes:", indentation_multiplier)
                notetypes = self.get_notetypes_by_obj(note)
                for notetype in notetypes:
                    self.print_indented(notetype, indentation_multiplier + 1)
            else:
                truncated_body = note.body.split('.')[0]
                self.print_indented("Body: {0}...".format(truncated_body), indentation_multiplier)
        else:
            print("<li>{0} ({1})</li>".format(note.body, note.notetype))

    def do_note(self, line):
        current_note = self.get_current_note()
        if current_note is None:
            return

        if line == "links":
            self.get_links(current_note)
            return

        truncated = True
        if line != "":
            truncated = False

        self.get_note_with_child_notes(current_note, truncated)
        print("")
        return

    def do_get_next_note(self, line):
        print("")
        if self.child_notes == []:
            print("No notes at current level.")
            print("")
            return
        elif self.child_note_index >= len(self.child_notes):
            print("Returning to the first note at the current level.")
            print("")
            self.child_note_index = 0

        note = self.child_notes[self.child_note_index]

        self.print_indented("Notetype: {0}".format(note.notetype))
        self.print_indented("Body: {0}".format(note.body))
        self.print_indented("Attached notetypes:")
        notetypes = self.get_notetypes_by_obj(note)
        for notetype in notetypes:
            self.print_indented(notetype, 2)
        self.child_note_index += 1
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

        verbose = True
        if line == "clean":
            verbose = False

        truncated = True
        if line != "":
            truncated = False

        # note_list = self.db.get_all_notes_by_obj(self.current_doc)
        note_list = self.get_notes_by_obj(self.current_doc)
        if note_list == []:
            print("")
            print("No notes to show.")
            print("")
            return

        if verbose == False:
            print("<ul>")
        note_index = 0
        for note in note_list:
            self.note_tree_helper(note, depth, note_index, truncated=truncated, verbose=verbose)
            note_index += 1

        if verbose == True:
            print("")
        else:
            print("</ul>")

    def note_tree_helper(self, current_note, depth, note_index, truncated=True, verbose=True):
        truncate = truncated
        if depth == 1:
            truncate = False

        if verbose == True:
            print("")
            self.print_indented("[Note {0}:]".format(note_index), depth)
        self.print_note_info(current_note, depth, truncate, verbose=verbose)
        note_list = self.get_notes_by_obj(current_note)
        if note_list == []:
            return
        else:
            if verbose == False:
                print("<ul>")
            child_note_index = 0
            for note in note_list:
                self.note_tree_helper(note, depth+1, child_note_index, truncated, verbose=verbose)
                child_note_index += 1
            if verbose == False:
                print("</ul>")

    def get_note_with_child_notes(self, current_note, truncated=True):
        self.note_tree_helper(current_note, 1, "and Children", truncated=truncated)
        return

    def do_EOF(self, line):
        return True

    def postloop(self):
        print

if __name__ == '__main__':
    try:
        LitreviewShell().cmdloop()
    except KeyboardInterrupt:
        print("^C")
