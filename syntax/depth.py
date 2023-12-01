#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 14:57:54 2020

@author: Lab
"""
import spacy
import re
from manual_parse import constituency_parse, dependency_parse
import os
from graphviz import Digraph
from PyPDF2 import PdfFileMerger
import pandas as pd

sentence_splitter = spacy.load('en_core_web_sm')

class ConstituencyTree:
    ID_NO = 0
    def __init__(self, node_type, children=None, word=None):
        self.id = ConstituencyTree.ID_NO
        ConstituencyTree.ID_NO += 1
        #Node type is whether a node is an S, NP, JJ, etc.
        self.node_type = node_type
        self.children = children
        self.parent = None
        self.is_leaf = False
        if not self.children:
            self.is_leaf = True
        else:
            #Linking child nodes to their parents is essential
            #for the Frazier and Yngve algorithms
            for child in self.children:
                child.parent = self
        #This attaches leaf nodes to the word they correspond with, i.e.: JJ: 'red'
        self.word = word

    def __repr__(self):
        #The repr displays as a nested list if pasted into a browser
        inner = self.word if self.word else ''.join(
                [f'<li>{child}</li>' for child in self.children]
                )
        return f'<ol>{self.node_type}: {inner}</ol>'

    def frazier_yngve_graph(self, dot = None, parent = None,
                            leaf_graph = None, path = None, view=False):
        #This generates a graph of the constituency tree with frazier and yngve score details.
        final = True
        if not dot:
            dot = Digraph()
            dot.graph_attr['rankdir'] = 'BT'
            leaf_graph = Digraph(name='leaves')
            leaf_graph.graph_attr['rank'] = 'min'
        else:
            final = False
        content = f'''{self.node_type}: {self.word}
            {self.leaf_yngve}|{self.leaf_frazier}''' \
            if self.is_leaf else f'''{self.node_type}
            {self.nodal_yngve}|{self.nodal_frazier}'''
        dot.node(str(self.id), content)
        if parent:
            dot.edge(str(self.id), str(parent))
        if not self.is_leaf:
            for child in self.children:
                child.frazier_yngve_graph(dot, self.id, leaf_graph=leaf_graph)
        if self.is_leaf:
            leaf_graph.node(str(self.id), content)
        if final:
            dot.subgraph(leaf_graph)
            if not path:
                path = self.words + '_ct.gz'
            dot.render(path, view=view)

    @property
    def words(self):
        if not hasattr(self, '_words'):
            self._words = ' '.join([leaf.word for leaf in self.leaves])
        return self._words

    @property
    def nodal_yngve(self):
        #This is equivalent to how many places to the left of the rightmost node
        #A given node is among its siblings, starting at 0
        if not hasattr(self, '_nodal_yngve'):
            if self.parent:
                for i, child in enumerate(self.parent.children[::-1]):
                    child._nodal_yngve = i
            else:
                self._nodal_yngve = 0
        return self._nodal_yngve

    @property
    def leaf_yngve(self):
        #This is the sum of the nodal_yngve scores of a node and all of its ancestors
        if not hasattr(self, '_leaf_yngve'):
            self._leaf_yngve = self.nodal_yngve
            handle = self
            while handle.parent:
                self._leaf_yngve += handle.parent.nodal_yngve
                handle = handle.parent
        return self._leaf_yngve

    @property
    def leaves(self):
        if not hasattr(self, '_leaves'):
            if self.is_leaf:
                self._leaves = [self]
            else:
                self._leaves = [leaf for child in self.children
                                for leaf in child.leaves]
        return self._leaves

    @property
    def nodal_frazier(self):
        #This is 0 if a node is not the leftmost of its siblings, 1.5 if it is
        #and is the child of an S node, and 1 otherwise
        if not hasattr(self, '_nodal_frazier'):
            if self.parent:
                if self.parent.children.index(self) == 0:
                    if self.parent.node_type == "S":
                        self._nodal_frazier = 1.5
                    else:
                        self._nodal_frazier = 1
                else:
                    self._nodal_frazier = 0
            else:
                self._nodal_frazier = 0
        return self._nodal_frazier

    @property
    def leaf_frazier(self):
        #This is the sum of the node and all of its ancestors' nodal frazier scores
        #Stopping when an ancester with nodal score of 0 is reached
        if not hasattr(self, '_leaf_frazier'):
            self._leaf_frazier = self.nodal_frazier
            if self._leaf_frazier == 0:
                return self._leaf_frazier
            handle = self
            while handle.parent:
                if handle.parent.nodal_frazier == 0: break
                self._leaf_frazier += handle.parent.nodal_frazier
                handle = handle.parent
        return self._leaf_frazier

    @property
    def num_clauses(self):
        if not hasattr(self, '_num_clauses'):
            is_clause = 1 if self.node_type == 'S' else 0
            if self.children:
                self._num_clauses = sum([child.num_clauses for child
                                      in self.children]) + is_clause
            else:
                self._num_clauses = is_clause
        return self._num_clauses

    @property
    def total_words(self):
        return len(self.leaves)

    @property
    def verb_count(self):
        if not hasattr(self, '_verb_count'):
            self.tally_parts_of_speech()
        return self._verb_count

    @property
    def adj_count(self):
        if not hasattr(self, '_adj_count'):
            self.tally_parts_of_speech()
        return self._adj_count

    @property
    def noun_count(self):
        if not hasattr(self, '_noun_count'):
            self.tally_parts_of_speech()
        return self._noun_count

    @property
    def adverb_count(self):
        if not hasattr(self, '_adverb_count'):
            self.tally_parts_of_speech()
        return self._adverb_count

    @property
    def det_count(self):
        if not hasattr(self, '_det_count'):
            self.tally_parts_of_speech()
        return self._det_count

    @property
    def personal_pronoun_count(self):
        if not hasattr(self, '_personal_pronoun_count'):
            self.tally_parts_of_speech()
        return self._personal_pronoun_count

    @property
    def conj_count(self):
        if not hasattr(self, '_conj_count'):
            self.tally_parts_of_speech()
        return self._conj_count

    @property
    def prep_count(self):
        if not hasattr(self, '_prep_count'):
            self.tally_parts_of_speech()
        return self._prep_count

    @property
    def properN_count(self):
        if not hasattr(self, '_properN_count'):
            self.tally_parts_of_speech()
        return self._properN_count


    def tally_parts_of_speech(self):
        self._noun_count, self._adj_count, self._adverb_count, \
            self._verb_count, self._det_count, self._personal_pronoun_count,\
            self._conj_count, self._prep_count, self._properN_count \
            = 0, 0, 0, 0, 0, 0, 0, 0, 0
        type_dict = {'V': '_verb_count',
                     'JJ': '_adj_count',
                     'N': '_noun_count',
                     'RB': '_adverb_count',
                     'DT': '_det_count',
                     'PRP': '_personal_pronoun_count',
                     'CC': '_conj_count',
                     'IN': '_prep_count',
                     'NNP': '_properN_count',
        }
        self._fine_type_dict = {}
        self._word_count = 0

        for leaf in self.leaves:
            for k, v in type_dict.items():
                nt = leaf.node_type
                if nt.startswith(k):
                    setattr(self, v, getattr(self, v) + 1)
                self._fine_type_dict[nt] = self._fine_type_dict.get(nt, 0) + 1
            self._word_count += 1
        self._percent_fine_type_dict = {k: 100*(v / self._word_count) for k, v in self._fine_type_dict.items()} 

    @property
    def total_Ydepth(self):
        #Sum of the leaf yngve scores of all of the leaves in this tree
        if not hasattr(self, '_total_Ydepth'):
            self._total_Ydepth = sum([leaf.leaf_yngve for leaf in self.leaves])
        return self._total_Ydepth

    @property
    def total_Fdepth(self):
        #Sum of the leaf frazier scores of all of the leaves in this tree
        if not hasattr(self, '_total_Fdepth'):
            self._total_Fdepth =  sum([leaf.leaf_frazier for leaf in self.leaves])
        return self._total_Fdepth

    @property
    def mean_Ydepth(self):
        #Mean yngve score of the leaves
        return self.total_Ydepth / len(self.leaves)

    @property
    def mean_Fdepth(self):
        #mean frazier score of the leaves
        return self.total_Fdepth / len(self.leaves)

    @property
    def max_Ydepth(self):
        return max([leaf.leaf_yngve for leaf in self.leaves])

    @property
    def max_Fdepth(self):
        return max([leaf.leaf_frazier for leaf in self.leaves])

    @staticmethod
    def constituency_parse(sentence, engine='allennlp'):
        #Generates the constituency parse tree, delegating to an engine which actually
        #does the parsing
        return {'allennlp': ConstituencyTree.allen_constituency_parse}[
                engine
                ](sentence)

    @classmethod
    def allen_constituency_parse(cls, sentence):
        import allen_constituency_parse
        #Generates the allennlp parse tree. This parse tree requires further
        #translation to create an instance of the ConstituencyTree class
        return ConstituencyTree.allen_constituency_process(
                    allen_constituency_parse.constituency_parse(sentence)[
                    'hierplane_tree'
                    ]['root']
                )

    @classmethod
    def allen_constituency_process(cls, parse_dict):
        #Translates the allennlp constituency parsetree into a Constituency
        #Tree instance
        node_type = parse_dict['nodeType']
        children = None
        if 'children' in parse_dict.keys():
            children = []
            for child in parse_dict['children']:
                children.append(cls.allen_constituency_process(child))
        else:
            return ConstituencyTree(node_type, children, parse_dict['word'])
        return ConstituencyTree(node_type, children)


class DependencyTree:
    #this class represents itself as a list of relations with no further structure
    def __init__(self):
        self.relations = []
        self.start_positions = []

    def __repr__(self):
        inner =  ''.join([
            f'''r.head: {r['head']} @ {r['head_pos']},
            relation_type: {r['relation_type']},
            tail: {r['tail']} @ {r['tail_pos']}'''
                for r in self.relations])
        return f'<ul>{inner}</ul>'

    @property
    def words(self):
        if not hasattr(self, '_words'):
            max_ = 0
            for r in self.relations:
                if r['head_pos'] > max_: max_ = r['head_pos']
                if r['tail_pos'] > max_: max_ = r['tail_pos']
            self._words = [''] * (max_ + 1)
            for r in self.relations:
                self._words[r['head_pos']] = r['head']
                self._words[r['tail_pos']] = r['tail']
            self._words = ' '.join(self._words)
        return self._words

    def graph(self, path=None, view=False):
        dot = Digraph()
        for r in self.relations:
            dot.node(str(r['head_pos']), r['head'])
            dot.node(str(r['tail_pos']), r['tail'])
            dot.edge(str(r['head_pos']), str(r['tail_pos']), label=r['relation_type'])
        if not path:
            path = self.words + '_dt.gv'
        dot.render(path, view=view)

    def add(self, head, head_pos, relation_type, tail, tail_pos):
        self.relations.append({
                'head': head,
                'head_pos': head_pos,
                'relation_type': relation_type,
                'tail': tail,
                'tail_pos': tail_pos
                })

    @property
    def total_SynDepLen(self):
        #sum of the length of the relations in this dependency tree
        if not hasattr(self, '_total_SynDepLen'):
            self._total_SynDepLen = sum([
                   abs(r['head_pos'] - r['tail_pos']) for r in self.relations
                    ])
        return self._total_SynDepLen

    @property
    def mean_SynDepLen(self):
        #mean length of the relations in this dependency tree
        return self.total_SynDepLen / len(self.relations)

    @property
    def max_SynDepLen(self):
        if not hasattr(self, '_max_SynDepLen'):
            self._max_SynDepLen = max([abs(r['head_pos'] - r['tail_pos']) for r in self.relations])
        return self._max_SynDepLen

    @staticmethod
    def dependency_parse(sentence, engine='allennlp'):
        #generates the dependency tree with a given engine
        return {'allennlp': DependencyTree.allen_dependency_parse}[
                engine
                ](sentence)

    @classmethod
    def allen_dependency_parse(cls, sentence):
        import allen_dependency_parse
        #generates an allennlp parsed dependency tree
        #further translation is required to create a DependencyTree instance
        return DependencyTree.allen_dependency_process(
                    allen_dependency_parse.dependency_parse(sentence)[
                    'hierplane_tree'
                    ]['root']
                )

    def preprocess(self, parse_dict):
        #Translates character positions of leaf nodes into word positions.
        #Allennlp does not generate word positions when parsing.
        self.start_positions.append(parse_dict['spans'][0]['start'])
        if 'children' in parse_dict.keys():
            for child in parse_dict['children']:
                self.preprocess(child)

    @classmethod
    def allen_dependency_process(cls, parse_dict, dependency_tree = None):
        #translates allennlp dependency tree into an instance of DependencyTree
        if 'children' not in parse_dict.keys(): return
        if not dependency_tree:
            dependency_tree = DependencyTree()
            dependency_tree.preprocess(parse_dict)
            dependency_tree.start_positions.sort()
        head = parse_dict['word']
        head_pos = parse_dict['spans'][0]['start']
        head_pos = dependency_tree.start_positions.index(head_pos)
        for child in parse_dict['children']:
            relation_type = child['link']
            tail = child['word']
            tail_pos = child['spans'][0]['start']
            tail_pos = dependency_tree.start_positions.index(tail_pos)
            dependency_tree.add(head, head_pos, relation_type, tail, tail_pos)
            cls.allen_dependency_process(child, dependency_tree)
        return dependency_tree

def get_statistics(sentence, engine='allennlp'):
    #Gets all of the statistics printed out in the example files for a given sentence
    ct = ConstituencyTree.constituency_parse(sentence, engine)
    ct.tally_parts_of_speech()
    dt = DependencyTree.dependency_parse(sentence, engine)
    return {
            'sentence_text': sentence,
            'num_clauses': ct.num_clauses,
            'mean_Fdepth': ct.mean_Fdepth,
            'total_Fdepth': ct.total_Fdepth,
            'max_Fdepth': ct.max_Fdepth,
            'mean_Ydepth': ct.mean_Ydepth,
            'total_Ydepth': ct.total_Ydepth,
            'max_Ydepth': ct.max_Ydepth,
            'mean_SynDepLen': dt.mean_SynDepLen,
            'total_SynDepLen': dt.total_SynDepLen,
            'max_SynDepLen': dt.max_SynDepLen,
            'noun_count': ct.noun_count,
            'adj_count': ct.adj_count,
            'adverb_count': ct.adverb_count,
            'verb_count': ct.verb_count,
            'det_count': ct.det_count,
            'conj_count': ct.conj_count,
            'prep_count': ct.prep_count,
            'properN_count': ct.properN_count,
            'pronoun_count': ct._personal_pronoun_count,
            'POS_counts': ct._fine_type_dict,
            'word_count': ct._word_count,
            'POS_portions': ct._percent_fine_type_dict,
    }

class Paragraph:
    def __init__(self, engine='allennlp', **kwargs):
        assert ('text' in kwargs or ('constituency_trees' in kwargs and 'dependency_trees' in kwargs))
        if 'text' in kwargs:
            self.text = kwargs['text']
            self.sentences = [str(sentence) for sentence in
                sentence_splitter(kwargs['text']).sents]
            self.constituency_trees = []
            self.dependency_trees = []
            for each in self.sentences:
                ct = ConstituencyTree.constituency_parse(each, engine)
                dt = DependencyTree.dependency_parse(each, engine)
                if ct != None:
                    ct.tally_parts_of_speech()
                    self.constituency_trees.append(ct)
                if dt != None:
                    self.dependency_trees.append(dt)
        elif 'constituency_trees' in kwargs:
            self.constituency_trees = kwargs['constituency_trees']
            self.dependency_trees = kwargs['dependency_trees']
            self.sentences = [ct.words for ct in self.constituency_trees]

    @property
    def statistics_per_sentence(self):
        if not hasattr(self, '_statistics_per_sentence'):
            self._statistics_per_sentence = [
                {
                'sentenceID': i,
                'sentence_text': sentence,
                'num_clauses': ct.num_clauses,
                'mean_Fdepth': ct.mean_Fdepth,
                'total_Fdepth': ct.total_Fdepth,
                'max_Fdepth': ct.max_Fdepth,
                'mean_Ydepth': ct.mean_Ydepth,
                'total_Ydepth': ct.total_Ydepth,
                'max_Ydepth': ct.max_Ydepth,
                'mean_SynDepLen': dt.mean_SynDepLen,
                'total_SynDepLen': dt.total_SynDepLen,
                'max_SynDepLen': dt.max_SynDepLen,
                'noun_count': ct.noun_count,
                'adj_count': ct.adj_count,
                'adverb_count': ct.adverb_count,
                'verb_count': ct.verb_count,
                'det_count': ct.det_count,
                'conj_count': ct.conj_count,
                'prep_count': ct.prep_count,
                'properN_count': ct.properN_count,
                'pronoun_count': ct._personal_pronoun_count,
                'POS_counts': ct._fine_type_dict,
                'word_count': ct._word_count,
                'POS_portions': ct._percent_fine_type_dict,
                } for i, sentence, ct, dt in zip(
                        range(len(self.sentences)),
                        self.sentences, self.constituency_trees,
                        self.dependency_trees)
            ]
        return self._statistics_per_sentence

    def __repr__(self):
            return f"""sentenceID|sentence_text|num_clauses|mean_Fdepth|total_Fdepth|mean_Ydepth|total_Ydepth|mean_SynDepLen|total_SynDepLen|noun_count|adj_count|adverb_count|verb_count|det_count|conj_count|prep_count|properN_count
        {"".join([f'''{s["sentenceID"]}|{s["sentence_text"]}|{s["num_clauses"]}|{s["mean_Fdepth"]}|{s["total_Fdepth"]}|{s["mean_Ydepth"]}|{s["total_Ydepth"]}|{s["mean_SynDepLen"]}|{s["total_SynDepLen"]}|{s["noun_count"]}|{s["adj_count"]}|{s["adverb_count"]}|{s["verb_count"]}|{s["det_count"]}|{s["conj_count"]}|{s["prep_count"]}|{s["properN_count"]}|{s["pronoun_count"]}|{s["POS_counts"]}|{s["word_count"]}{s["POS_portions"]}
        '''
        for s in self.statistics_per_sentence])}"""
    #def graph(self):
        #paths = []
        #for ct, dt, i in zip(self.constituency_trees, self.dependency_trees, range(len(self.constituency_trees))):
            #ctpath = self.dirname + '/' + str(i) + '_ct.gz'
            #dtpath = self.dirname + '/' + str(i) + '_dt.gz'
            #paths.append(ctpath + '.pdf')
            #paths.append(dtpath + '.pdf')
            #ct.frazier_yngve_graph(view=False, path=ctpath)
            #dt.graph(view=False, path=dtpath)
        #merger = PdfFileMerger()
        #for file in paths:
            #merger.append(file)
        #merger.write(self.dirname + '/' + 'sentence_diagrams.pdf')
        #for file in paths:
            #os.remove(file)
            #os.remove(file[:-4])

def process_sentences(text):
    """This is a function made specifically to imitate the format of the example.txt.dat files
    that were part of the original project, as is not intended to be part of the public api.
    """
    #Breaks up a text into sentences and gets statistics and returns a printable representation
    #of the collected statistics.
    sentences = sentence_splitter(text).sents
    dicts = [{**get_statistics(str(sentence)), **{'sentenceID': i}}
        for i, sentence in enumerate(sentences)
    ]
    return f"""sentenceID|sentence_text|num_clauses|mean_Fdepth|total_Fdepth|mean_Ydepth|total_Ydepth|mean_SynDepLen|total_SynDepLen|noun_count|adj_count|adverb_count|verb_count|det_count|conj_count|prep_count|properN_count
    {"".join([f'''{s["sentenceID"]}|{s["sentence_text"]}|{s["num_clauses"]}|{s["mean_Fdepth"]}|{s["total_Fdepth"]}|{s["mean_Ydepth"]}|{s["total_Ydepth"]}|{s["mean_SynDepLen"]}|{s["total_SynDepLen"]}|{s["noun_count"]}|{s["adj_count"]}|{s["adverb_count"]}|{s["verb_count"]}|{s["det_count"]}|{s["conj_count"]}|{s["prep_count"]}|{s["properN_count"]}|{s["pronoun_count"]}|{s["POS_counts"]}|{s["word_count"]}{s["POS_portions"]}
    '''
    for s in dicts])}"""

def get_paragraph_statistics(text):
    """Returns a list of dictionaries corresponding to the statistics of each sentence in paragraph text."""
    sentences = sentence_splitter(text).sents
    return [{**get_statistics(str(sentence)), **{'sentenceID': i}}
        for i, sentence in enumerate(sentences)
    ]

def parse_manual_annotated(text, dirname):
    """This is a function made specifically to parse the format of the Validation_GK_S1.txt and other files
    that were part of the original project, and is not intended to be part of the public api.
    """
    start_text_position = re.search(r'Here:', text).span()[1]
    try:
        str_position = re.search(r'Str:', text).span()[0]
    except AttributeError:
        str_position = len(text) - 1
    root_positions = [r.span()[1] for r in re.finditer(r'\(ROOT', text)]
    def find_closing_parenthesis(subtext):
        par_count = 0
        for i, c in enumerate(subtext):
            if c == '(':
                par_count += 1
            elif c == ')':
                par_count -= 1
            if par_count < 0:
                return i
    root_end_positions = [rp + find_closing_parenthesis(text[rp:])
        for rp in root_positions
    ]
    auto_paragraph = Paragraph(text=text[start_text_position: root_positions[0] - 6], dirname=dirname + '_auto')
    constituency_trees = [
            constituency_parse(text[rp:rep]) for rp, rep in zip(root_positions, root_end_positions)
            ]
    auto_manual_sentences = [ct.words for ct in constituency_trees]
    dependency_trees = [
            dependency_parse(text[rep + 2: n - 6]) for rep, n in zip(root_end_positions, root_positions[1:] + [str_position + 6])
            ]
    am_constituency_trees = [ConstituencyTree.constituency_parse(s) for s in auto_manual_sentences]
    am_dependency_trees = [DependencyTree.dependency_parse(s) for s in auto_manual_sentences]
    manual_paragraph = Paragraph(constituency_trees=constituency_trees,
                                             dependency_trees=dependency_trees, dirname=dirname + '_manual')
    auto_manual_paragraph = Paragraph(constituency_trees=am_constituency_trees,
                                      dependency_trees=am_dependency_trees, dirname=dirname + '_automanual')
    return auto_paragraph, manual_paragraph, auto_manual_paragraph


def process_multiple_manual(paths, dirnames):
    """This is a function made specifically to parse the format of the Validation_GK_S1.txt and other files
    that were part of the original project, and is not intended to be part of the public api.
    """
    stat_list = []
    for path, dirname in zip(paths, dirnames):
        with open(path) as f: text = f.read()
        auto_paragraph, manual_paragraph, auto_manual_paragraph = \
            parse_manual_annotated(text, dirname)
        auto_paragraph.graph()
        manual_paragraph.graph()
        auto_manual_paragraph.graph()
        auto_stats = auto_paragraph.statistics_per_sentence
        manual_stats = manual_paragraph.statistics_per_sentence
        auto_manual_stats = auto_manual_paragraph.statistics_per_sentence

        for i, (a, m) in enumerate(zip(auto_manual_stats, manual_stats)):
            stat_list.append({
                'index': dirname + str(i + 1),
                'Max Y': m['max_Ydepth'],
                'Auto Max Y': a['max_Ydepth'],
                'Total Y': m['total_Ydepth'],
                'Auto_Total Y': a['total_Ydepth'],
                'Max F': m['max_Fdepth'],
                'Auto Max F': a['max_Fdepth'],
                'Total F': m['total_Fdepth'],
                'Auto Total F': a['total_Fdepth'],
                'Total Dep': m['total_SynDepLen'],
                'Auto Total Dep': a['total_SynDepLen'],
                'Max Dep': m['max_SynDepLen'],
                'Auto Max Dep': a['max_SynDepLen'],
                    })
    df = pd.DataFrame(stat_list)
    df.to_csv('complexity_Jacob.csv')


def process_constituency_manual(path, dirname):
    with open(path) as f: text = f.read()
    constituency_tree = constituency_parse(text)



def main(docs, args):
    retval = {}
    for docname, text in docs.items():
        p = Paragraph(text=text)
        #if graph:
            #p.graph()
        stats = p.statistics_per_sentence
        stat_list = []
        for i, a in enumerate(stats):
            stat_list.append({
                    'index': docname + str(i + 1),
                                    'sentence_text': re.sub(',', 'COMMA', a['sentence_text']),
                                    'num_clauses': a['num_clauses'],
                                    'mean_Fdepth': a['mean_Fdepth'],
                                    'total_Fdepth': a['total_Fdepth'],
                                    'max_Fdepth': a['max_Fdepth'],
                                    'mean_Ydepth': a['mean_Ydepth'],
                                    'total_Ydepth': a['total_Ydepth'],
                                    'max_Ydepth': a['max_Ydepth'],
                                    'mean_SynDepLen': a['mean_SynDepLen'],
                                    'total_SynDepLen': a['total_SynDepLen'],
                                    'max_SynDepLen': a['max_SynDepLen'],
                                    'noun_count': a['noun_count'],
                                    'adj_count': a['adj_count'],
                                    'adverb_count': a['adverb_count'],
                                    'verb_count': a['verb_count'],
                                    'det_count': a['det_count'],
                                    'conj_count': a['conj_count'],
                                    'prep_count': a['prep_count'],
                                    'properN_count': a['properN_count'],
                                    })
        df = pd.DataFrame(stat_list)
        retval[docname] = df.to_json()
    return retval
