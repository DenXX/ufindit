
import os
import sys
import re

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _PROJECT_DIR)
sys.path.insert(0, os.path.dirname(_PROJECT_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ufindit.settings")

from bs4 import BeautifulSoup
from httpproxy.models import Request
from nltk import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import numpy as np
import sklearn
from sklearn import tree, linear_model
from sklearn.dummy import DummyClassifier
from sklearn.neighbors import KNeighborsClassifier
from ufindit.utils import get_tokens
from urlparse import urlsplit, urlunsplit

from query_url_problems.models import QueryUrlJudgement
from query_url_problems.html_document import HtmlDocuments

class QueryUrlProblemTraining:
    """ Processes query-url judgements data for training"""
    def __init__(self):
        self._stemmer = PorterStemmer()
        self._missing_term_data = []
        self._misinterpreted_term_data = []
        self._missing_relation_data = []
        self._docs = HtmlDocuments()
        self._term_freq = {}
        self._term_total_count = 0
        with open('unigram.dat', 'r') as input:
            for line in input:
                word, count = line.strip().split()
                word = self._stemmer.stem(word)
                count = int(count)
                if word not in self._term_freq:
                    self._term_freq[word] = 0
                self._term_freq[word] += count
                self._term_total_count += count

    def _get_page_html(self, qu_judgement, url):
        """ Returns html of a page for the given qu_judgement or None if it is not in cache"""

        parsed_url = urlsplit(url)
        # TODO: we should also match with querystring
        url = urlunsplit((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', parsed_url.fragment))
        try:
            matching_request = Request.objects.filter(path=url)
            if len(matching_request) > 1:
                return None
            matching_request = matching_request.all()[0]
        except:
            return None
        # Replacing encoding because of the bug in our version of lxml parser. Should be fixed in lxml > 3.0
        return matching_request.response.content.replace('ISO-8859-1', 'utf-8').replace('iso-8859-1', 'utf-8').encode('utf-8')


    def _get_stems(self, text):
        """ Returns sentences with stems for the current text """

        sents = map(word_tokenize, sent_tokenize(text))
        for index in xrange(len(sents)):
            sents[index] = map(self._stemmer.stem, sents[index])
        return [stem for sent in sents for stem in sent] # Flatten list


    def process_judgement(self, qu_judgement):
        """ Processes query-url judgement and adds training examples to theinternal lists """

        # If no useful labels
        if qu_judgement.missing_terms == '' and \
           qu_judgement.misinterpreted_terms == '' and \
           qu_judgement.missing_relations == '':
           return

        # Get web page html from cache
        url = qu_judgement.url.replace('http/', 'http://').replace('https/', 'https://')
        html = self._get_page_html(qu_judgement, url)
        if not html: return
        html_doc = self._docs.get_doc(url, html)

        query_stems = self._get_stems(qu_judgement.serp.query)
        task_stems = self._get_stems(qu_judgement.task.text)

        # Get labels, terms are separated with ','
        missing_terms_labels = map(self._stemmer.stem, set(filter(lambda x: len(x) > 0,
            qu_judgement.missing_terms.strip().split(','))))
        misinterpreted_terms_labels = map(self._stemmer.stem, set(filter(lambda x: len(x) > 0,
            qu_judgement.misinterpreted_terms.strip().split(','))))
        missing_relations_labels = map(self._stemmer.stem, set(filter(lambda x: len(x) > 0,
            qu_judgement.missing_relations.strip().split(','))))

        for term in query_stems:
            # If term is missing
            if term in missing_terms_labels:
                self._missing_term_data.append((True, term, query_stems, task_stems, html_doc, url))
            else: # If present
                self._missing_term_data.append((False, term, query_stems, task_stems, html_doc, url))
                if term in misinterpreted_terms_labels:
                    self._misinterpreted_term_data.append((True, term, query_stems, task_stems, html_doc, url))
                else:
                    self._misinterpreted_term_data.append((False, term, query_stems, task_stems, html_doc, url))

        for term1 in query_stems:
            for term2 in query_stems:
                if term1 == term2 or term2 in self._missing_term_data or\
                   term2 in self._missing_term_data: continue
                if term1 in missing_relations_labels and term2 in missing_relations_labels:
                    self._missing_relation_data.append((True, (term1, term2), query_stems, task_stems, html_doc, url))
                else:
                    self._missing_relation_data.append((False, (term1, term2), query_stems, task_stems, html_doc, url))

    def get_term_features(self, example):
        features = []
        target, term, query_stems, task_stems, html_doc, url = example
        features.append(1 if term in self._term_freq else 0) # Is it in dictionary
        features.append(1.0 * self._term_total_count / self._term_freq[term] if term in self._term_freq else 0) # ICF
        features.append(1 if term in html_doc else 0) # Occur in doc
        features.append(html_doc.count(term)) # Number of occurances

        # Tag type
        tags = html_doc.get_term_tags(term)
        tagsoi = ['title', 'h1', 'h2', 'h3', 'h4', 'div', 'a', 'li', 'p', 'script']
        tags_feats = [0, ] * len(tagsoi)
        occurances = 0
        text_tokens_in_tag = 0
        for tag in tags:
            if tag.name in tagsoi:
                tags_feats[tagsoi.index(tag.name)] += 1
            text_tokens_in_tag += html_doc.get_tag_token_count(tag)
            occurances += 1
        features.extend(tags_feats)
        features.append(1.0 * text_tokens_in_tag / (occurances + 1))

        # Distance between query terms in tokens
        term_positions = html_doc.get_term_flat_pos(term)
        min_dist = html_doc.get_term_count()
        ave_dist = 0
        ave_dist_normalizer = 0
        # Distance to other tokens from query
        same_tag = 0
        other_query_stems_count = 0
        for tag in tags:
            for query_stem in filter(lambda stem: stem != term, query_stems):
                other_query_stems_count += 1
                query_stem_tags = html_doc.get_term_tags(query_stem)
                for query_stem_tag in query_stem_tags:
                    if tag == query_stem_tag:
                        same_tag += 1

                # Now flat positions
                query_term_positions = html_doc.get_term_flat_pos(query_stem)
                for pos1 in term_positions:
                    for pos2 in query_term_positions:
                        min_dist = min([min_dist, abs(pos1 - pos2)])
                        ave_dist += abs(pos1 - pos2)
                        ave_dist_normalizer += 1

        features.append(1.0 * same_tag / (other_query_stems_count + 1))
        features.append(min_dist)
        features.append(1.0 * ave_dist / (ave_dist_normalizer + 1))

        return features

    def train_missing_term_model(self):
        nn_classifier = KNeighborsClassifier(n_neighbors=1, algorithm='auto')
        lr_classifier = linear_model.LogisticRegression(penalty='l1')
        tree_classifier = tree.DecisionTreeClassifier()
        dummy_classifier = DummyClassifier(strategy='most_frequent')
        targets = []
        features = []
        for example in self._missing_term_data:
            target = 1 if example[0] else -1
            feats = self.get_term_features(example)
            targets.append(target)
            features.append(feats)
            print target, " ".join(map(str, feats)), example[-1], " ".join(map(str, example[:3]))
            # print target, feats, example

        print "Missing term data training (LogReg): ", sklearn.cross_validation.cross_val_score(lr_classifier, np.array(features), np.array(targets), cv=10)
        print "Missing term data training (3NN): ", sklearn.cross_validation.cross_val_score(nn_classifier, np.array(features), np.array(targets), cv=10)
        print "Missing term data training (tree): ", sklearn.cross_validation.cross_val_score(tree_classifier, np.array(features), np.array(targets), cv=10)
        print "Missing term data training (dummy): ", sklearn.cross_validation.cross_val_score(dummy_classifier, np.array(features), np.array(targets), cv=10)

def main():
    training_data = QueryUrlProblemTraining()
    count = 0
    import datetime
    for qu_judgement in QueryUrlJudgement.objects.all():
        print count, datetime.datetime.now()
        # Skip some pathological example
        if count != 254:
            training_data.process_judgement(qu_judgement)
        count += 1

    print "Missing term:", sum(1 for x in training_data._missing_term_data if x[0]), len(training_data._missing_term_data), 1.0 * sum(1.0 for x in training_data._missing_term_data if x[0]) / len(training_data._missing_term_data)
    print "Misinterpreted term:", sum(1 for x in training_data._misinterpreted_term_data if x[0]), len(training_data._misinterpreted_term_data), 1.0 * sum(1.0 for x in training_data._misinterpreted_term_data if x[0]) / len(training_data._misinterpreted_term_data)
    print "Missing relation:", sum(1 for x in training_data._missing_relation_data if x[0]), len(training_data._missing_relation_data), 1.0 * sum(1.0 for x in training_data._missing_relation_data if x[0]) / len(training_data._missing_relation_data)
    training_data.train_missing_term_model()

if __name__ == "__main__":
    main()
