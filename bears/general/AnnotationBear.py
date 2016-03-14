from coalib.parsing.StringProcessing.Core import (search_for,
                                                  search_in_between,
                                                  unescaped_search_in_between)
from coalib.bearlib.languages.LanguageDefinition import LanguageDefinition
from coalib.results.SourceRange import SourceRange
from coalib.bears.LocalBear import LocalBear
from coalib.results.HiddenResult import HiddenResult


class AnnotationBear(LocalBear):

    def run(self, filename, file: str, language: str, language_family: str):
        """
        Finds out all the positions of comments and strings in a file.
        The Bear searches for valid comments and strings
        and yields them as HiddenResults with the appropriate ranges.
        Invalid comments or strings are:
        1. Comments within comments,
        2. Comments within strings and
        3. Strings within comments.
        """
        file = ''.join(file)
        annot_dict = {}
        annot_dict['comment'] = {}
        annot_dict['string'] = {}
        annot_dict['string']['multiline'] = {}
        annot_dict['string']['singleline'] = {}
        annot_dict['comment']["singleline"] = {}
        annot_dict['comment']["multiline"] = {}
        # Tuple of tuples containing start and end of annotations
        match_pos = ()
        lang_dict = LanguageDefinition(language, language_family)

        annot_dict['comment']["singleline"].update(
                    lang_dict["comment_delimiter"])

        annot_dict['comment']["multiline"].update(
                    lang_dict["multiline_comment_delimiters"])

        annot_dict['string']['singleline'].update(
                                            lang_dict["string_delimiters"])
        annot_dict['string']['multiline'].update(
                                       lang_dict["multiline_string_delimiters"])
        multi_str = single_str = multi_comm = ()
        search_dict = annot_dict['string']['multiline']
        multi_str = find_string_comment(file, search_dict, True)
        search_dict = annot_dict['string']['singleline']
        single_str = find_string_comment(file, search_dict, True)
        search_dict = annot_dict['comment']["multiline"]
        multi_comm = find_string_comment(file, search_dict, False)

        match_pos += single_str + multi_str + multi_comm
        # Seperate since single-line comments don't have a definite start and
        # end
        search_dict = annot_dict['comment']["singleline"]
        single_comm = find_singleline_comments(file, search_dict, match_pos)
        match_pos += single_comm
        match_pos = remove_nested(match_pos)
        m_comm = s_comm = m_str = s_str = []
        if match_pos:
            m_comm = list(get_range(file, filename, match_pos, multi_comm))
            s_comm = list(get_range(file, filename, match_pos, single_comm))
            m_str = list(get_range(file, filename, match_pos, multi_str))
            s_str = list(get_range(file, filename, match_pos, single_str))
        yield HiddenResult(self, m_comm)
        yield HiddenResult(self, s_comm)
        yield HiddenResult(self, m_str)
        yield HiddenResult(self, s_str)


def get_range(file, filename, match_pos, string_comment):
    """
    Checks if range is valid and then yields it.
    """
    search_range = []
    for i in string_comment:
        if i in match_pos:
            search_range.append(i)
    search_range = [(calc_line_col(file, start), calc_line_col(file, end))
                    for (start, end) in search_range]

    for i in search_range:
        yield SourceRange.from_values(filename,
                                      start_line=i[0][0],
                                      start_column=i[0][1],
                                      end_line=i[1][0],
                                      end_column=i[1][1])


def find_string_comment(file, annot, escape):
    """
    gives all instances of strings or multiline comments found within
    the file, even if they are nested in other strings or comments
    """
    if escape:
        search_func = unescaped_search_in_between
    else:
        search_func = search_in_between
    found_pos = ()
    for annot_type in annot:
        found_pos += tuple(search_func(annot_type, annot[annot_type], file))
    if found_pos:
        found_pos = tuple((i.begin.range[0], i.end.range[1])
                          for i in found_pos)
    return found_pos


def find_singleline_comments(file, annot, match_pos):
    """
    Finds all single-line comments outside of other string or comments.
    """
    single_comm = []
    for comment_type in annot:
        for i in search_for(comment_type, file):
            if not in_range_list(match_pos, (i.start(), i.end())):
                end = file.find('\n', i.start())
                if end != -1:
                    single_comm.append((i.start(), end))
                else:
                    end = len(file) + 1
                    single_comm.append((i.start(), end))
    return tuple(single_comm)


def in_range_list(outside_range_list, inside_range):
    """
    finds if a given 'range' is inside a any of the 'ranges' in
    a list of ranges.
    """
    for outside_range in outside_range_list:
        if inside_range == outside_range:
            continue

        elif inside_range[0] == outside_range[0]:
            if inside_range[1] < outside_range[1]:
                return True

        elif inside_range[0] in range(outside_range[0], outside_range[1]):
            return True
    return False


def calc_line_col(file, pos_to_find):
    """
    Calculate line number and column in the file, from position.
    """
    line = 1
    pos = -1
    pos_new_line = file.find('\n')
    while True:
        if pos_new_line == -1:
            return (line, pos_to_find-pos)

        if pos_to_find <= pos_new_line:
            return (line, pos_to_find - pos)

        else:
            line += 1
            pos = pos_new_line
            pos_new_line = file.find('\n', pos_new_line + 1)


def remove_nested(match_pos):
    """
    removes all the entries from a listthat are nested
    inside some other entry of that list.
    """
    unnested_list = []
    for i in match_pos:
        if not in_range_list(match_pos, i):
            unnested_list.append(i)
    return tuple(unnested_list)
