
import bs4
from nltk import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import string

class HtmlDocuments:
    """ Maintains a collection of Html documents """
    def __init__(self):
        self._docs = {}

    def get_doc(self, url, html_code):
        if url in self._docs: return self._docs[url]
        self._docs[url] = HtmlDocument(html_code)
        return self._docs[url]

class HtmlDocument:
    """
    Parsed HTML document with additional info on text tokens
    """
    def __init__(self, html_code, stem=True, remove_stopwords=True):
        self._html_code = html_code
        self._doc = None
        self._title = None
        self._doc_tokens = None
        self._index = {}
        self._stemmer = PorterStemmer() if stem else None
        self._stopwords = set(stopwords.words('english')) if remove_stopwords else None
        # Parse and index
        self._parse_page(html_code)
        self._build_text_index(self._doc)

    def _parse_page(self, html_code):
        self._doc = bs4.BeautifulSoup(html_code, 'html5lib')
        self._title = self._get_tokens(self._doc.find('title').get_text()) if self._doc.find('title') else None
        self._doc_tokens = self._get_tokens(self._doc.find('body').get_text()) if self._doc.find('body') else None

    def _get_tokens(self, text):
        if text is None: return None

        sent_tokens = map(word_tokenize, sent_tokenize(text))
        for index in xrange(len(sent_tokens)):
            sent = filter(lambda token: token not in self._stopwords, map(string.lower, sent_tokens[index]))
            if self._stemmer:
                sent = map(self._stemmer.stem, sent)
            sent = filter(lambda term: len(term) > 0 and term.isalnum(), sent)
            sent_tokens[index] = sent
        return [stem for sent in sent_tokens for stem in sent]

    def _index_token(self, token, node, pos):
        """ Inserts token occurance into internal map index """
        if token not in self._index:
            self._index[token] = [[node, [pos]], ]
        else:
            if node != self._index[token][-1][0]:
                self._index[token].append([node, [pos]])
        self._index[token][-1][1].append(pos)


    def _build_text_index(self, node):
        """ Builds index of tokens on web page """
        nodes = [node, ]
        while len(nodes) > 0:
            cur_node = nodes.pop()
            pos = 0
            tokens = []
            text_children = []
            for child in cur_node.children:
                if isinstance(child, bs4.element.NavigableString):
                    # Remove text, we will add tokens instead
                    text_children.append(child)
                    for token in self._get_tokens(child):
                        tokens.append(token)
                        self._index_token(token, cur_node, pos)
                        pos += 1
                else:
                    nodes.append(child)

            # Remove text nodes and add individual tokens
            map(lambda x: x.extract(), text_children)
            map(cur_node.append, tokens)

    def __contains__(self, term):
        """ Returns true if the given token exists in the document """
        return term in self._index.keys()

    def count(self, term):
        if term not in self._index: return 0
        return reduce(lambda prev_count, node_positions: prev_count + len(node_positions[1]), self._index[term], 0)

    def get_term_tags(self, term):
        """ Returns a list of tags where the current term occurs """
        if term not in self: return []
        return [node_positions[0] for node_positions in self._index[term]]

    def _traverse_down(self, tag, callback):
        """ Traverses DOM down from the current node and calls callback for each child """
        nodes = []
        nodes.append(tag)
        while len(nodes) > 0:
            node = nodes.pop()
            for child in node.children:
                callback(child)
                if isinstance(child, bs4.element.Tag):
                    nodes.append(child)

    def get_tag_token_count(self, tag):
        """ Returns the number of text tokens in and below current tag """

        # Make list as a workaround, if count is just integer,
        # assignment inside nested method will consider it a local var
        count = [0, ]
        def count_tokens(child):
            if isinstance(child, bs4.element.NavigableString):
                count[0] += 1

        self._traverse_down(tag, count_tokens)
        return count[0]

    def get_links_count(self, tag):
        """ Returns the number of link tags in and below current tag """
        count = [0, ]

        def count_anchors(child):
            if isinstance(child, bs4.element.Tag) and child.name == 'a':
                count[0] += 1

        self._traverse_down(tag, count_anchors)
        return count[0]

    def get_term_flat_pos(self, term):
        """ Returns a list of positions of the token in document text """
        return [pos for pos, doc_term in enumerate(self._doc_tokens) if term == doc_term]

    def get_term_count(self):
        return len(self._doc_tokens)

    def __repr__(self):
        return str(self._title)


if __name__ == "__main__":
    from sys import argv
    import urllib2
    #html_code = urllib2.urlopen(argv[1]).read()
    #doc = HtmlDocument(html_code)
    doc = HtmlDocument(argv[1])
    print doc.count(argv[2])