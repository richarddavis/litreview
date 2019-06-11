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
        self.prompt = u'(litr) '
        self.db = Database()
        self.current_paper = None
        self.notes_at_current_level = []
        self.note_index_at_current_level = 0
        self.note_history = []
        self.cite_history = []
        self.all_papers = self.db.get_papers()

    def reset(self):
        self.prompt = u'(litr) '
        self.current_paper = None
        self.notes_at_current_level = []
        self.note_index_at_current_level = 0
        self.note_history = []

    def update_prompt(self):
        if self.current_paper is None:
            return
        truncated_title = self.current_paper.title[:40]
        self.prompt = u'(litr: ' + truncated_title + u'...) '

    def reload_papers(self):
        self.all_papers = self.db.get_papers()

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

    def do_add_paper(self, line):
        print("")
        paper_dict = {}
        try:
            paper_dict[u'title'] = input('Paper title: ')
        except EOFError:
            return

        print("")
        paper_dict[u'authors'] = []
        try:
            while input('Add author? Y/n: ').lower() == u'y':
                lastname = input('Author Last Name: ')
                firstname = input('Author First Name: ')
                paper_dict[u'authors'].append({u'lastname':lastname, u'firstname':firstname, u'paper_count':u'0'})
                print("")
        except EOFError:
            return

        print("")
        try:
            year = input('Year: ')
        except EOFError:
            return
        if year is not None:
            paper_dict[u'year'] = year
            print("")

        try:
            doi = input('DOI: ')
        except EOFError:
            return
        if doi is not "":
            paper_dict[u'doi'] = doi
            print("")

        paper = Paper(**paper_dict)
        self.db.add_paper(paper)
        self.all_papers = self.db.get_papers()

    def do_delete_paper(self, line):
        print("")
        if line == "" and self.current_paper is not None:
            # Delete self.current_paper
            self.print_indented("Selected paper: {0}".format(self.current_paper.title))
            try:
                if input("Delete this paper? Y/n: ").lower() == u'y':
                    deleted = self.db.delete_paper(self.current_paper)
                    if deleted == True:
                        self.reset()
                        self.reload_papers()
                        print("")
                        print("Paper deleted.")
                        print("")
                        return
                    else:
                        print("")
                        print("Error: Paper not deleted.")
                        print("")
                        return
            except EOFError:
                return
        else:
            while not (line != "" and line.isnumeric() and int(line) < len(self.all_papers) and int(line) >= 0):
                print("")
                paper_index = 0
                for paper in self.all_papers:
                    self.print_indented("[{0}]: {1}".format(paper_index, paper.title))
                    paper_index += 1
                    print("")
                try:
                    line = input('Please select a paper: ')
                except EOFError:
                    return

            self.print_indented("Selected paper: {0}".format(self.all_papers[int(line)].title))
            try:
                if input("Delete this paper? Y/n: ").lower() == u'y':
                    deleted = self.db.delete_paper(self.all_papers[int(line)])
                    if deleted == True:
                        self.reset()
                        self.reload_papers()
                        print("")
                        print("Paper deleted.")
                        print("")
                        return
                    else:
                        print("")
                        print("Paper deletion canceled.")
                        print("")
                        return
            except EOFError:
                return

    def do_show_papers(self, line):
        paper_index = 0
        for paper in self.all_papers:
            self.do_show_paper_info(str(paper_index))
            paper_index += 1

    def do_select_paper(self, line):
        while not (line != "" and line.isnumeric() and int(line) < len(self.all_papers) and int(line) >= 0):
            print("")
            paper_index = 0
            for paper in self.all_papers:
                self.print_indented("[{0}]: {1}".format(paper_index, paper.title))
                paper_index += 1
                print("")
            try:
                line = input('Please select a paper: ')
            except EOFError:
                return

        self.reset()
        self.current_paper = self.all_papers[int(line)]
        self.update_prompt()
        self.notes_at_current_level = self.get_notes_at_current_level(self.current_paper)
        self.do_show_note_tree("")

    def do_show_paper_info(self, line):
        print("")
        paper = None
        if line != "" and line.isnumeric():
            if int(line) >= len(self.all_papers) or int(line) < 0:
                print("That paper does not exist.")
                print("")
                return
            else:
                paper = self.all_papers[int(line)]
                self.print_indented("[{}]".format(line))
        else:
            if self.current_paper == None:
                print("Please select a paper first.")
                print("")
                return
            else:
                paper = self.current_paper
        self.print_indented("Title: {0}".format(paper.title))
        self.print_indented("Authors:")
        for author in paper.authors:
            self.print_indented("{0}, {1}".format(author[u'lastname'], author[u'firstname']), 2)
        self.print_indented("DOI: {0}".format(paper.doi))
        self.print_indented("Year: {0}".format(paper.year))
        self.print_indented("Number of notes: {0}".format(len(self.db.get_notes(paper))))
        print("")

    def do_add_citation_link(self, line):
        print("")
        line = ""
        paper_index = 0
        while not (line != "" and line.isnumeric() and int(line) < len(self.all_papers) and int(line) >= 0):
            for paper in self.all_papers:
                self.print_indented("[{0}]: {1}".format(paper_index, paper.title))
                paper_index += 1
                print("")
            try:
                line = input('Please select the CITING paper: ')
            except EOFError:
                return
        citing_paper = self.all_papers[int(line)]

        print("")
        line = ""
        paper_index = 0
        while not (line != "" and line.isnumeric() and int(line) < len(self.all_papers) and int(line) >= 0):
            for paper in self.all_papers:
                self.print_indented("[{0}]: {1}".format(paper_index, paper.title))
                paper_index += 1
                print("")
            try:
                line = input('Please select the CITED paper: ')
            except EOFError:
                return
        cited_paper = self.all_papers[int(line)]

        self.db.add_citation(citing_paper, cited_paper)

    def do_citations(self, line):
        if self.current_paper is None:
            print("")
            print("Please select a paper first.")
            print("")
            return
        citing = self.current_paper.citing
        self.print_indented("Citing:")
        index_map = {}
        current_index = 0
        for citing_paper_id in citing:
            master_index = 0
            for paper in self.all_papers:
                if citing_paper_id == paper.id:
                    self.print_indented("[{0}]: {1}".format(current_index, paper.title), 2)
                    index_map[current_index] = master_index
                    print("")
                master_index += 1
            current_index += 1

        cited_by = self.current_paper.cited_by
        self.print_indented("Cited by:")
        for cited_by_id in cited_by:
            master_index = 0
            for paper in self.all_papers:
                if cited_by_id == paper.id:
                    self.print_indented("[{0}]: {1}".format(current_index, paper.title), 2)
                    index_map[current_index] = master_index
                    print("")
                master_index += 1
            current_index += 1

        line = input('Jump to paper: ')

        if not (line != "" and line.isnumeric() and int(line) < len(index_map) and int(line) >= 0):
            return

        self.cite_history.append(self.current_paper)
        self.reset()
        self.current_paper = self.all_papers[index_map[int(line)]]
        self.update_prompt()
        self.notes_at_current_level = self.get_notes_at_current_level(self.current_paper)
        self.do_show_note_tree("")

    def do_pop_citation(self, line):
        if self.cite_history == []:
            print("")
            print("Already at beginning.")
            print("")
            return
        self.reset()
        self.current_paper = self.cite_history.pop()
        self.update_prompt()
        self.notes_at_current_level = self.get_notes_at_current_level(self.current_paper)
        self.do_show_note_tree("")

    def get_notetypes_by_obj(self, target_obj):
        if self.current_paper is None:
            print("")
            print("Please select a paper first.")
            print("")
            return
        all_notes = self.db.get_notes(self.current_paper)
        return list({note.notetype for note in all_notes if note.ref_id == target_obj.id})

    def get_notes_by_obj(self, target_obj):
        if self.current_paper is None:
            print("")
            print("Please select a paper first.")
            print("")
            return
        all_notes = self.db.get_notes(self.current_paper)
        return [note for note in all_notes if note.ref_id == target_obj.id]

    def do_add_note(self, line):
        print("")
        note_dict = {}
        if self.current_paper == None:
            print("Pleast select a paper first.")
            print("")
            return

        target_obj = None
        if self.note_history == []:
            target_obj = self.current_paper
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
        self.db.add_note(note, self.current_paper)
        self.notes_at_current_level = self.get_notes_at_current_level(target_obj)

    def do_delete_note(self, line):
        print("")
        if line == "" and self.get_current_note() is not None:
            # Delete self.get_current_note()
            current_note = self.get_current_note()
            self.print_indented("Selected note: {0}".format(current_note.title))
            try:
                if input("Delete this note? Y/n: ").lower() == u'y':
                    deleted = self.db.delete_note(self.current_paper, current_note)
                    if deleted == True:
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
                    self.print_indented("[{0}]: {1}".format(note_index, note.title))
                    note_index += 1
                    print("")
                try:
                    line = input('Please select a note: ')
                except EOFError:
                    return

            self.print_indented("Selected note: {0}".format(self.notes_at_current_level[int(line)].title))
            try:
                if input("Delete this note? Y/n: ").lower() == u'y':
                    deleted = self.db.delete_note(self.current_paper, self.notes_at_current_level[int(line)])
                    if deleted == True:
                        print("")
                        print("Note deleted.")
                        print("")
                        return
                    else:
                        print("")
                        print("Cancelled note deletion.")
                        print("")
                        return
            except EOFError:
                return

    def do_show_notes(self, line):
        print("")
        if self.current_paper == None:
            print("Please select a paper first.")
            print("")
            return

        if self.notes_at_current_level == []:
            print("No notes at current level.")
            print("")
            return

        note_index = 0
        for note in self.notes_at_current_level:
            self.print_indented("[Note {0}:]".format(note_index))
            self.show_note_info(note)
            note_index += 1
            print("")

    def do_select_note(self, line):
        while not (line != "" and line.isnumeric() and int(line) < len(self.notes_at_current_level) and int(line) >= 0):
            self.do_show_notes("")
            try:
                line = input('Please select a note: ')
            except EOFError:
                return

        self.note_history.append(self.notes_at_current_level[int(line)])
        self.notes_at_current_level = self.get_notes_at_current_level(self.get_current_note())
        self.do_show_notes("")

    def do_pop_note(self, line):
        if self.note_history == []:
            print("")
            print("Already at top level.")
            print("")
            return

        self.note_history.pop()

        if self.note_history == []:
            self.notes_at_current_level = self.get_notes_at_current_level(self.current_paper)
        else:
            self.notes_at_current_level = self.get_notes_at_current_level(self.get_current_note())

        self.do_show_notes("")

    def get_notes_at_current_level(self, target_obj):
        if self.current_paper is None:
            print("")
            print("Please select a paper first.")
            print("")
            return
        all_notes = self.db.get_notes(self.current_paper)
        notes_at_current_level = []
        for note in all_notes:
            if note.ref_id == target_obj.id:
                notes_at_current_level.append(note)
        self.note_index_at_current_level = 0
        return notes_at_current_level

    def show_note_info(self, current_note, indentation_multiplier=1):
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

    def do_show_note_info(self, line):
        print("")
        cn = None
        if self.notes_at_current_level == []:
            print("No notes to show.")
            print("")
            return
        elif line == "":
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

    def do_show_note_tree(self, line):
        depth = 1
        root_node = self.current_paper
        if root_node is None:
            print("")
            print("No paper selected.")
            print("")
            return
        if self.current_paper.id is None:
            print("")
            print("Currently selected paper has no id.")
            print("")
            return

        # note_list = self.db.get_all_notes_by_obj(self.current_paper)
        note_list = self.get_notes_by_obj(self.current_paper)
        if note_list == []:
            print("")
            print("No notes to show.")
            print("")
            return
        note_index = 0
        for note in note_list:
            self.show_note_tree_helper(note, depth, note_index)
            note_index += 1
            print("")

    def show_note_tree_helper(self, current_note, depth, note_index):
        print("")
        self.print_indented("[Note {0}:]".format(note_index), depth)
        self.show_note_info(current_note, depth)
        note_list = self.get_notes_by_obj(current_note)
        if note_list == []:
            return
        else:
            child_note_index = 0
            for note in note_list:
                self.show_note_tree_helper(note, depth+1, child_note_index)
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
