from nltk.tokenize.punkt import PunktWordTokenizer
from nltk.corpus import stopwords

def get_tokens(text, remove_stopwords=True):
    tokenizer = PunktWordTokenizer()
    return [term for term in tokenizer.tokenize(text.lower()) \
        if (len(term) > 1 or term.isalpha()) and \
        (term not in stopwords.words('english') or (not remove_stopwords))]
