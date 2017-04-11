#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot finds grammar errors in Hebrew. See README.md for more details.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-xml              Retrieve information from a local XML dump (pages-articles
                  or pages-meta-current, see https://download.wikimedia.org).
                  Argument can also be given as "-xml:filename".

-fix              Run the bot in automatic fix mode. USE WITH CAUTION.

Please type "misparim.py -help | more" if you can't read the top of the help.
"""
from __future__ import unicode_literals
import re
import HspellPy

import pywikibot
from pywikibot import pagegenerators
from pywikibot import xmlreader
from pywikibot.diff import PatchManager
from pywikibot import i18n

__author__ = 'eran'

# make sure the dictionary path can be found. Otherwise you would have to explicitly set the path:
# HspellPy.set_dictionary_path('../hspell/hebrew.wgz')

speller = HspellPy.Hspell(linguistics=True)
safe_eser_zachar = '(?<!אחת.)(?<!שתים.)(?<!שלוש.)(?<!ארבע.)(?<!חמש.)(?<!שש.)(?<!שבע.)(?<!שמונה.)(?<!תשע.)עשרה'
# no 8 - looks similar in both
# no 7 in zachar - because also mean at the time
zachar_rgx = re.compile(
    '(?<!(?<!על) פי)( ו?[משכלב]?)((?<!מצד )שני|שלושה|ארבעה|חמישה|שישה|שבעה|תשעה|' + safe_eser_zachar +
    '|שלושת|ארבעת|חמשת|ששת|שמונת|תשעת|עשרת) ([א-ת]{2,}|\[\[[א-ת]{2,}(?=\]\][^א-ת])|\[\[[^\]]+?\|[א-ת]{2,}(?=\]\][^א-ת]))',
    re.U)
safe_eser_nekeva = '(?<!אחד.)(?<!שניים.)(?<!שנים.)(?<!שלושה.)(?<!ארבעה.)(?<!חמישה.)(?<!חמשה.)(?<!ששה.)(?<!שישה.)(?<!שבעה.)(?<!שמונה.)(?<!תשעה.)עשר'
# no 10 in nekeva because of 12-19 in zachar
nekeva_rgx = re.compile(
    '(?!(?<!על) פי)(?<! בת)( ו?[משכלב]?)(שתי|שלוש|ארבע|חמש|שש|שבע|תשע|' + safe_eser_nekeva +
    ') ([א-ת]{2,}|\[\[[א-ת]{2,}(?=\]\][^א-ת])|\[\[[^\]]+?\|[א-ת]{2,}(?=\]\][^א-ת]))', re.U)
pi_regex = re.compile('(?<!על) פי (?:שתיים|שלוש|ארבע|חמש|שש|שבע|תשע|עשר) (?!מאות)', re.U)

remove_cites = re.compile('\{\{ציטוט(?:[^{]+?|\{\{[^{]+?\}\}).+\}\}')

remove_wiki = re.compile('\[\[.+?\||\[\[')
guess_gender = True

# GrammarError = namedtuple('GrammarError', ['word', 'usage', 'fix'])


class GrammarError(object):
    def __init__(self, match, is_male):
        self._match = match
        self._is_male = is_male  # is the correct form is male?

    @property
    def word(self):
        return self._match[2]

    @property
    def usage(self):
        return self._match[1]

    def fix(self, text):
        if self._is_male:
            correct = self.to_male()
        else:
            correct = self.to_female()
        in_correct = '{}{} {}'.format(self._match[0], self._match[1], self._match[2])
        return re.sub(in_correct, correct, text)

    def to_female(self):
        male_to_female = {
            'שני': 'שתי',
            'שלושה': 'שלוש',
            'ארבעה': 'ארבע',
            'חמישה': 'חמש',
            'שישה': 'שש',
            'שבעה': 'שבע',
            'תשעה': 'תשע',
            'עשרה': 'עשר',
            'שלושת': 'שלוש',
            'ארבעת': 'ארבע',
            'חמשת': 'חמש',
            'ששת': 'שש',
            'שבעת': 'שבע',
            'תשעת': 'תשע',
            'עשרת': 'עשר'
        }

        return '{}{} {}'.format(self._match[0], male_to_female[self._match[1]], self._match[2])

    def to_male(self):
        female_to_male = {
            'שתי': 'שני',
            'שלוש': 'שלושה',
            'ארבע': 'ארבעה',
            'חמש': 'חמישה',
            'שש': 'שישה',
            'שבע': 'שבעה',
            'תשע': 'תשעה',
            'עשר': 'עשרה',
        }

        return '{}{} {}'.format(self._match[0], female_to_male[self._match[1]], self._match[2])


def check_zachar_nekeva_old(text, check_pi=True):
    # no 8 - looks similar in both
    # no 7 in zachar - because also mean at the time
    # no 10 in nekeva because of 12-19 in zachar
    text = remove_cites.sub('', text)  # remove quotes
    possible_errors = []
    zachars = zachar_rgx.findall(text)
    nekvas = nekeva_rgx.findall(text)
    allowed_prefixes = ['', 'ה']

    # for word_list, expectation in [(zachars, 'ע,ז'), (nekvas, 'ע,נ')]:
    for word_list, expectation, is_male in [(zachars, re.compile('[^,]+?,ז'), False),
                                            (nekvas, re.compile('[^,]+?,נ'), True)]:
        # check only known words
        known_words = [word_use for word_use in word_list if word_use[2] in speller]

        words_splits = [speller.enum_splits(word[2]) for word in known_words]

        # if it has meaning with not allowed prefix (example: be-emzaut) skip it
        words_for_check = [(word, wsplit) for word, wsplit in zip(known_words, words_splits)
                           if not any((word[2][:pos_split.preflen] not in allowed_prefixes or pos_split.baseword == ''
                                       for pos_split in wsplit))]

        # all possible morpological analysis
        linginfos = [(word, [morph.linginfo for pos_split in wsplit for morph in speller.linginfo(pos_split.baseword)])
                     for word, wsplit in words_for_check]

        # only rabim nouns for sure
        # linginfos = [(word, morphos) for word, morphos in linginfos if all(morph.startswith('ע') and 'רבים' in morph
        #                                                                    for morph in morphos)]
        linginfos = [(word, morphos) for word, morphos in linginfos if
                     all('רבים' in morph for morph in morphos) and
                     any(morph.startswith('ע') for morph in morphos)]

        for word, morphos in linginfos:
            # incorrect = not any((morph.startswith(expectation)) for morph in morphos)
            incorrect = not any(expectation.match(morph) for morph in morphos)
            # not both zachar and nekeva (example: panim)
            incorrect &= not any(morph.startswith('ע,ז,נ') for morph in morphos)
            if incorrect:
                possible_errors.append(GrammarError(word, is_male))

    # pi
    if check_pi:
        incorrect_pi = pi_regex.findall(text)
        possible_errors += [GrammarError(['פי ', pi_nek, ''], True) for pi_nek in incorrect_pi]
    return possible_errors


def check_zachar_nekeva(text, check_pi=True):
    text = remove_cites.sub('', text)  # remove quotes
    possible_errors = []
    zachars = zachar_rgx.findall(text)
    nekvas = nekeva_rgx.findall(text)
    allowed_prefixes = ['', 'ה']
    has_zachar_nekva_data = re.compile('.+,[זנ](,|$)')
    # for word_list, expectation in [(zachars, 'ע,ז'), (nekvas, 'ע,נ')]:
    for word_list, expectation, is_male in [(zachars, re.compile('[^,]+?,ז'), False),
                                            (nekvas, re.compile('[^,]+?,נ'), True)]:
        # check only known words
        for number_prefix, number, word in word_list:
            clean_word = remove_wiki.sub('', word)
            if clean_word not in speller:
                if not guess_gender:
                    continue
                # possible different spelling - skip
                if speller.try_correct(clean_word):
                    continue
                guess_male = clean_word.endswith('ים')
                guess_female = clean_word.endswith('ות')

                if (guess_male or guess_female) and guess_male == is_male:
                    possible_errors.append(GrammarError((number_prefix, number, word), is_male))
            else:
                word_split = speller.enum_splits(clean_word)
                # if it has meaning with not allowed prefix (example: be-emzaut) skip it
                if any((clean_word[:pos_split.preflen] not in allowed_prefixes or pos_split.baseword == ''
                        for pos_split in word_split)) or not any(word_split):
                    continue

                # all possible morphological analysis
                linginfos = [morph.linginfo for pos_split in word_split
                             for morph in speller.linginfo(pos_split.baseword)]

                if not all('רבים' in morph for morph in linginfos) or \
                        any(not has_zachar_nekva_data.match(morph) for morph in linginfos):
                    continue

                # incorrect = not any((morph.startswith(expectation)) for morph in morphos)
                incorrect = not any(expectation.match(morph) for morph in linginfos)
                # not both zachar and nekeva (example: panim)
                incorrect &= not any(morph.startswith('ע,ז,נ') for morph in linginfos)
                if incorrect:
                    possible_errors.append(GrammarError((number_prefix, number, word), is_male))

    # pi
    if check_pi:
        incorrect_pi = pi_regex.findall(text)
        possible_errors += [GrammarError(['פי ', pi_nek, ''], True) for pi_nek in incorrect_pi]
    return possible_errors


def xml_dump_gen(xml_filename, query):
    site = pywikibot.Site()
    dump = xmlreader.XmlDump(xml_filename)
    parser = dump.parse()
    for entry in parser:
        if entry.ns != '0' or entry.isredirect:
            continue

        possible_errors = query(entry.text)
        if possible_errors:
            yield pywikibot.Page(site, entry.title)


def run(gen, allow_fix=False, summary=None):
    error_types = dict()
    try:
        for page in gen:
            try:
                errors = check_zachar_nekeva(page.get(get_redirect=True), not allow_fix)
                if allow_fix:
                    orig_text = page.get(get_redirect=True)
                    new_text = orig_text
                    for err in errors:
                        if 'דברות' in err.word:
                            continue
                        new_text = err.fix(new_text)
                    if orig_text != new_text:
                        pywikibot.showDiff(orig_text, new_text)

                        # plt.clf()
                        pp = PatchManager('\n'.join(orig_text.split('.')), '\n'.join(new_text.split('.')))
                        for i, hunk in enumerate(pp.hunks):
                            print((' '.join(hunk.diff_plain_text.split(' ')[::-1])))
                            # plt.text(0.1, 0.8-i*0.1, hunk.diff_plain_text[::-1])
                        # plt.show()

                        choice = pywikibot.input_choice(
                            u'Do you want to accept these changes?',
                            [('Yes', 'y'), ('No', 'n')],
                            default='N')

                        if choice == 'y':
                            page.put_async(new_text, summary)

                else:
                    for err in errors:
                        if err.word not in error_types:
                            error_types[err.word] = [(page.title(), err.usage)]
                        else:
                            error_types[err.word].append((page.title(), err.usage))
            except pywikibot.NoPage:
                continue
    except KeyboardInterrupt:
        pass

    output_report = ''
    for err, pages in sorted([(err, pages) for err, pages in error_types.items()],
                             key=lambda x: len(set(p.title() for p, u in x[1]))):
        output_report += '\n*' + err
        page_usages = set(['*#[[{}]] - {}'.format(page.title(), usage) for page, usage in pages])
        output_report += '\n' + '\n'.join(sorted(page_usages))
    report_page = pywikibot.Page(pywikibot.Site(), 'ויקיפדיה:תחזוקה/שתי שקל')
    intro = '''
{{/פתיח}}
==רשימה לבדיקה==
'''
    report_page.put(intro+output_report, 'עדכון')


def main(*args):
    allow_fix = False
    edit_summary = '[[ויקיפדיה:תחזוקה/שתי שקל|שתי שקל]]'
    xml_filename = None

    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()
    gen = None
    for arg in local_args:
        if genFactory.handleArg(arg):
            continue
        if arg.startswith('-fix'):
            allow_fix = True
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xml_filename = i18n.input('pywikibot-enter-xml-filename')
            else:
                xml_filename = arg[5:]
        elif arg.startswith('-summary:'):
            edit_summary = arg[9:]

    if xml_filename:
        gen = xml_dump_gen(xml_filename, lambda x: check_zachar_nekeva(x, not allow_fix))
    gen = genFactory.getCombinedGenerator(gen)
    run(gen, allow_fix, edit_summary)


if __name__ == '__main__':
    main()
