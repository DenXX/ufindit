
import re
from sys import argv
import sklearn
from sklearn import tree, linear_model
from sklearn.dummy import DummyClassifier
from sklearn.neighbors import KNeighborsClassifier
from nltk.stem import LancasterStemmer
import numpy as np
from webpage_segmentation import SDAlgorithm

from ufindit.utils import get_tokens

stemmer = LancasterStemmer()

class FeatureGenerator:
    """ Generate features for a query-url problem """
    def __init__(self):
        pass


def stem_tokens(tokens):
    return map(stemmer.stem, tokens)

def get_features(example):
    label, term, query, task, doc_terms, html, url = example
    query_stems = map(stem_tokens, query)
    doc_stems = map(stem_tokens, doc_terms)
    target_stem = stemmer.stem(term)

    features = [doc_terms.count(term), 1 if term in doc_terms else 0, doc_terms.index(term) if term in doc_terms else -1, len(doc_terms), len(query), ]
    features += [doc_stems.count(target_stem), 1 if target_stem in doc_stems else 0, doc_stems.index(target_stem) if target_stem in doc_stems else -1,]

    # Webpage segmentation
    type, article, comments, multiple = SDAlgorithm().analyze_page_code(html)
    if article is not None:
        article_stems = stem_tokens(get_tokens(article.full_text))
        features += [1, article_stems.count(target_stem), 1 if target_stem in article_stems else 0, article_stems.index(target_stem) if target_stem in article_stems else -1,]
    else:
        features += [0, 0, 0, 0]


    # Calculate density of query terms
    if target_stem in doc_stems:
        query_terms_pos = set([])
        for query_stem in query_stems:
            if query_stem != target_stem:
                query_terms_pos.update([i for i, x in enumerate(doc_stems) if x == query_stem])
        min_dist = len(doc_stems)
        stem_pos = set([i for i, x in enumerate(doc_stems) if x == target_stem])
        for pos in query_terms_pos:
            for pos2 in stem_pos:
                min_dist = min((min_dist, abs(pos - pos2)))
        features += [min_dist, 1.0 * min_dist / len(doc_stems)]
    else:
        features += [len(doc_stems), 1.0]

    # HTML page features


    return np.array(features)

def train_missing_term_model(data):
    nn_classifier = KNeighborsClassifier(n_neighbors=1, algorithm='auto')
    lr_classifier = linear_model.LogisticRegression(penalty='l1')
    tree_classifier = tree.DecisionTreeClassifier()
    dummy_classifier = DummyClassifier(strategy='most_frequent')
    targets = []
    features = []
    for example in data:
        target = 1 if example[0] else -1
        feats = get_features(example)
        targets.append(target)
        features.append(feats)
        print target, " ".join(map(str, feats)), example[-1], " ".join(map(str, example[:3]))
        # print target, feats, example

    print "Missing term data training (LogReg): ", sklearn.cross_validation.cross_val_score(lr_classifier, np.array(features), np.array(targets), cv=10)
    print "Missing term data training (3NN): ", sklearn.cross_validation.cross_val_score(nn_classifier, np.array(features), np.array(targets), cv=10)
    print "Missing term data training (tree): ", sklearn.cross_validation.cross_val_score(tree_classifier, np.array(features), np.array(targets), cv=10)
    print "Missing term data training (dummy): ", sklearn.cross_validation.cross_val_score(dummy_classifier, np.array(features), np.array(targets), cv=10)
    model = tree_classifier.fit(features, targets)


def main(training_data_file):
    missing_term_data = []
    misinterpreted_term_data = []
    missing_relation_data = []

    missing_term_count = 0
    misinterpreted_term_count = 0
    missing_relation_count = 0
    total = 0
    with open(training_data_file, 'r') as input:
        for line in input:
            mt, m, mr, query, task, doc, url = line.split('\t')
            mt = set(filter(lambda x: len(x) > 0, mt.strip().split(',')))
            m = set(filter(lambda x: len(x) > 0, m.strip().split(',')))
            mr = set(filter(lambda x: len(x) > 0, mr.strip().split(',')))
            query = query.strip().split(',')
            task = task.strip().split(',')
            doc = filter(lambda x: len(x) > 0, doc.strip().split(','))

            added_missing = False
            added_misinterpreted = False
            added_missing_relation = False
            for term1 in query:
                # If term is missing
                if term1 in mt:
                    missing_term_data.append((True, term1, query, task, doc, url))
                    added_missing = True
                else: # If present
                    missing_term_data.append((False, term1, query, task, doc, url))
                    if term1 in m:
                        misinterpreted_term_data.append((True, term1, query, task, doc, url))
                        added_misinterpreted = True
                    else:
                        misinterpreted_term_data.append((False, term1, query, task, doc, url))
                        for term2 in mr:
                            if term1 == term2 or term2 in mt or term2 in m: continue
                            if term1 in mr and term2 in mr:
                                missing_relation_data.append((True, (term1, term2), query, task, doc, url))
                                added_missing_relation = True
                            else:
                                missing_relation_data.append((False, (term1, term2), query, task, doc, url))

            if len(mt) != 0:
                missing_term_count += len(mt)
                if not added_missing:
                    print "No missing: ", mt, m, mr, query
            if len(m) != 0:
                misinterpreted_term_count += len(m)
                if not added_misinterpreted:
                    print "No misinterpreted: ", mt, m, mr, query
            if len(mr) != 0:
                missing_relation_count += len(mr)
                if not added_missing_relation:
                    print "No missing relation: ", mt, m, mr, query

    print "Missing term:", sum(1 for x in missing_term_data if x[0]), len(missing_term_data), 1.0 * sum(1.0 for x in missing_term_data if x[0]) / len(missing_term_data), missing_term_count
    print "Misinterpreted term:", sum(1 for x in misinterpreted_term_data if x[0]), len(misinterpreted_term_data), 1.0 * sum(1.0 for x in misinterpreted_term_data if x[0]) / len(misinterpreted_term_data), misinterpreted_term_count
    print "Missing relation:", sum(1 for x in missing_relation_data if x[0]), len(missing_relation_data), 1.0 * sum(1.0 for x in missing_relation_data if x[0]) / len(missing_relation_data), missing_relation_count
    train_missing_term_model(missing_term_data)

if __name__ == "__main__":
    pass
