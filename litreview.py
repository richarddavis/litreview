from datetime import datetime
from time import sleep
from model import Model
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
        self.model = Model()
        self.child_notes = []

    def update_prompt(self):
        current_doc = self.model.get_current_doc()
        if current_doc is None:
            return
        truncated_title = current_doc.title[:40]
        self.prompt = u'(lr: ' + truncated_title + u'...) '

    def print_indented(self, formatted_text, indentation_multiplier = 1):
        print(textwrap.fill(formatted_text,
                            initial_indent = " " * self.INDENT * indentation_multiplier,
                            subsequent_indent  = " " * self.INDENT * indentation_multiplier,
                            width = 150))

    def do_history(self, line):
        print(self.model.history)

    def do_whereami(self, line):
        truncated = True
        if line != "":
            truncated = False

        if truncated == True:
            current_doc = self.model.get_current_doc()
            if current_doc is not None:
                self.print_indented("Current doc: {}...".format(current_doc.title[:40]))
            if self.get_current_note() is not None:
                self.print_indented("Current note: {}...".format(self.get_current_note().body[:40]))
        else:
            current_doc = self.model.get_current_doc()
            if current_doc is not None:
                self.print_indented("Current doc: {}".format(current_doc.title))
            if self.get_current_note() is not None:
                self.print_indented("Current note: {}".format(self.get_current_note().body))

    # TODO: Check that this problem is solved.
    # PROBLEM: When self.reload_docs() or self.reload_notes() is called,
    # link_history and note_history will both be corrupted.
    # Keep in mind that self.all_docs and self.all_notes are sorted, so simply replacing them
    # with a dict that maps ids to objects would not work.
    # One solution could be to keep a dict mapping id to the index in all_notes or all_docs.
    # Then, note_history and link_history could store ids, and pushing to and popping from
    # history could be managed by a helper function that accepts and returns objects, but
    # works with ids and indices internally.

    def get_docs(self):
        return self.model.get_docs()

    def get_notes(self):
        return self.model.get_notes()

    def set_current_obj(self, obj):
        self.model.set_current_obj(obj)

    def get_current_doc(self):
        return self.model.get_current_doc()

    def get_current_note(self):
        return self.model.get_current_note()

    def get_current_obj(self):
        return self.model.get_current_obj() # Returns obj or None

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
        self.model.add_doc(doc)

    def do_delete_doc(self, line):
        print("")
        current_doc = self.model.get_current_doc()
        if line == "" and current_doc is not None:
            # Delete current_doc
            self.print_indented("Selected doc: {0}".format(current_doc.title))
            try:
                if input("Delete this doc? Y/n: ").lower() == u'y':
                    deleted = self.model.delete_doc(current_doc)
                    if deleted == True:
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
            all_docs = self.get_docs()
            while not (line != "" and line.isnumeric() and int(line) < len(all_docs) and int(line) >= 0):
                print("")
                doc_index = 0
                for doc in all_docs:
                    self.print_indented("[{0}]: {1}".format(doc_index, doc.title))
                    doc_index += 1
                    print("")
                try:
                    line = input('Please select a doc: ')
                except EOFError:
                    return

            self.print_indented("Selected doc: {0}".format(all_docs[int(line)].title))
            try:
                if input("Delete this doc? Y/n: ").lower() == u'y':
                    # Need
                    deleted = self.model.delete_doc(all_docs[int(line)])
                    if deleted == True:
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
        all_docs = self.get_docs()
        for doc in all_docs:
            self.do_doc_info(str(doc_index))
            doc_index += 1
        print("")

    def do_select_doc(self, line):
        all_docs = self.get_docs()
        while not (line != "" and line.isnumeric() and int(line) < len(all_docs) and int(line) >= 0):
            print("")
            doc_index = 0
            for doc in all_docs:
                self.print_indented("[{0}]: {1}".format(doc_index, doc.title))
                doc_index += 1
                print("")
            try:
                line = input('Please select a doc: ')
            except EOFError:
                return

        self.set_current_obj(all_docs[int(line)])
        self.update_prompt()
        self.do_note_tree("")

    def do_doc(self, line):
        current_doc = self.model.get_current_doc()
        if current_doc is None:
            return

        if line == "links":
            self.get_links(current_doc)
            return
        else:
            print("")
            self.print_doc_info(current_doc)
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
        self.print_indented("Number of notes: {0}".format(len(doc.attached_notes))) # Do more with this

    def do_doc_info(self, line):
        doc = None
        all_docs = self.get_docs()
        if line != "" and line.isnumeric():
            if int(line) >= len(all_docs) or int(line) < 0:
                print("")
                print("That doc does not exist.")
                print("")
                return
            else:
                doc = all_docs[int(line)]
                print("")
                self.print_indented("[{}]".format(line))
        else:
            if self.get_current_doc() == None:
                print("")
                print("Please select a doc first.")
                print("")
                return
            else:
                doc = self.get_current_doc()

        self.print_doc_info(doc)

    def do_link(self, line):
        if self.get_current_doc() is None:
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
            all_docs = self.get_docs()
            while not (choice != "" and choice.isnumeric() and int(choice) < len(all_docs) and int(choice) >= 0):
                for doc in all_docs:
                    self.print_indented("[{0}]: {1}".format(doc_index, doc.title))
                    doc_index += 1
                    print("")
                try:
                    choice = input('Please select the doc to link to: ')
                except EOFError:
                    return
            in_obj = all_docs[int(choice)]
        elif link_to == "note":
            pass

        if in_obj is None:
            return

        if link_from == "doc":
            self.model.create_link(self.get_current_doc(), in_obj)
        elif link_from == "note":
            self.model.create_link(self.get_current_note(), in_obj)

    def do_delete_link(self, line):
        if self.get_current_doc() is None:
            print("")
            print("Please select a doc first.")
            print("")
            return

        outlinks = self.get_current_doc().outlinks
        if not outlinks:
            return None

        self.print_indented("Outlinks:")
        index_map = {}
        current_index = 0
        for outlinks_doc_id in outlinks:
            master_index = 0
            all_docs = self.get_docs()
            for doc in all_docs:
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

        all_docs = self.get_docs()
        deleted = self.model.delete_link(self.get_current_doc(), all_docs[index_map[int(line)]])
        if deleted == True:
            print("")
            print("Link deleted.")
            print("")
            return
        else:
            print("")
            print("Error: Link not deleted.")
            print("")
            return

    def do_links(self, line):
        self.get_links(self.get_current_obj())

    def get_links(self, obj=None):

        if obj is None:
            return

        outlinks = obj.outlinks
        inlinks = obj.inlinks

        link_list = []
        link_list_index = 0
        print("")

        if len(outlinks) > 0:
            self.print_indented("Outlinks:")
            for outlink_id in outlinks:
                if self.model.get_doc(outlink_id) is not None:
                    doc = self.model.get_doc(outlink_id)
                    link_list.append(doc)
                    print("")
                    self.print_indented("[{0}]: {1}".format(link_list_index, doc.title[:40]), 2)
                    link_list_index += 1
                elif self.model.get_note(outlink_id) is not None:
                    note = self.model.get_note(outlink_id)
                    link_list.append(note)
                    print("")
                    self.print_indented("[{0}]: {1}".format(link_list_index, note.body[:40]), 2)
                    link_list_index += 1
            print("")

        if len(inlinks) > 0:
            self.print_indented("Inlinks:")
            for inlink_id in inlinks:
                if self.model.get_doc(inlink_id) is not None:
                    doc = self.model.get_doc(inlink_id)
                    link_list.append(doc)
                    print("")
                    self.print_indented("[{0}]: {1}".format(link_list_index, doc.title[:40]), 2)
                    link_list_index += 1
                elif self.model.get_note(inlink_id) is not None:
                    note = self.model.get_note(inlink_id)
                    link_list.append(note)
                    print("")
                    self.print_indented("[{0}]: {1}".format(link_list_index, note.body[:40]), 2)
                    link_list_index += 1
            print("")

        if not link_list:
            return

        try:
            line = input('Jump to link: ')
        except EOFError:
            return

        if not (line != "" and line.isnumeric() and int(line) < len(link_list) and int(line) >= 0):
            print("")
            return

        jumping_to_obj = link_list[int(line)]

        self.set_current_obj(jumping_to_obj)
        self.update_prompt()

    def do_back(self, line):
        if self.model.history.back() is None:
            print("")
            print("At beginning of history.")
            print("")
            return

        self.update_prompt()

    def get_notetypes_by_obj(self, target_obj):
        if self.get_current_doc() is None:
            print("")
            print("Please select a doc first.")
            print("")
            return
        all_notes = self.get_notes()
        return list({note.notetype for note in all_notes if note.ref_id == target_obj.id})

    def get_notes_by_obj(self, target_obj):
        if self.get_current_doc() is None:
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

        target_obj = self.get_current_obj()
        if target_obj is None:
            print("Pleast select a doc first.")
            print("")
            return

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
        self.model.add_note(note, self.get_current_doc())

    def do_delete_note(self, line):
        print("")
        if line == "":
            current_note = self.get_current_note()
            if current_note is None:
                print ("No current note.")
                print ("")
                return None

            self.print_indented("Selected note: {0}".format(current_note.body))
            try:
                if input("Delete this note? Y/n: ").lower() == u'y':
                    deleted = self.model.delete_note(current_note, self.get_current_doc())
                    if deleted == True:
                        print("")
                        print ("Note deleted.")
                        print("")
                        return
                    else:
                        print("")
                        print ("Error: Note not deleted.")
                        print("")
                        return
                else:
                    print("")
                    print("Cancelled note deletion.")
                    print("")
                    return
            except EOFError:
                return
        else:
            child_notes = self.get_child_notes()
            while not (line != "" and line.isnumeric() and int(line) < len(child_notes) and int(line) >= 0):
                print("")
                note_index = 0
                for note in child_notes:
                    self.print_indented("[{0}]: {1}".format(note_index, note.body))
                    note_index += 1
                    print("")
                try:
                    line = input('Please select a note: ')
                except EOFError:
                    return

            self.print_indented("Selected note: {0}".format(child_notes[int(line)].body))
            try:
                if input("Delete this note? Y/n: ").lower() == u'y':
                    note_to_delete = child_notes[int(line)]
                    deleted = self.model.delete_note(note_to_delete, self.get_current_doc())
                    if deleted == True:
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
        current_obj = self.get_current_obj()
        if current_obj == None:
            print("")
            print("Please select a doc or note first.")
            print("")
            return

        if self.get_child_notes(current_obj) == []:
            print("")
            print("No attached notes.")
            print("")
            return

        truncated = True
        if line != "":
            truncated = False

        note_index = 0
        print("")
        for note in self.get_child_notes(current_obj):
            self.print_indented("[Note {0}:]".format(note_index))
            self.print_note_info(note, truncated=truncated)
            print("")
            note_index += 1

    def do_select_note(self, line):
        note_indices = line.split()
        if not note_indices:
            self.do_notes("")
            try:
                line = input('Please select a note: ')
                note_indices = [line]
            except EOFError:
                return

        display_notes = self.get_child_notes(self.get_current_obj())

        interim_note = None
        for ni in note_indices:
            if not (ni.isnumeric() and int(ni) < len(display_notes) and int(ni) >= 0):
                print("")
                print("No note selected.")
                print("")
                return
            else:
                interim_note = display_notes[int(ni)]
                display_notes = self.get_child_notes(interim_note)
                # print("temp_note is {}".format(temp_note))
                # print("get_child_notes() returned {}".format(self.child_notes))

        self.set_current_obj(interim_note)
        self.do_notes("")

    def get_child_notes(self, target_obj=None):
        target = target_obj
        if target is None:
            if self.get_current_obj() is None:
                print("")
                print("Please select a doc or note first.")
                print("")
                return
            else:
                target = self.get_current_obj()

        all_notes = self.get_notes()
        child_notes = []
        for note in all_notes:
            if note.ref_id == target.id:
                child_notes.append(note)

        child_notes.sort()
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

    def do_note_tree(self, line):
        depth = 1
        root_node = self.get_current_doc()
        if root_node is None:
            print("")
            print("No doc selected.")
            print("")
            return
        if root_node.id is None:
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

        note_list = self.get_notes_by_obj(self.get_current_doc())
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
