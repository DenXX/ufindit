"""
    This module implements search providers returning a set of search
    results for a query. You can create an instance of SearchProxy
    object passing the name of search to use and call its search(player, query)
    method to get search results.

    Author: Denis Savenkov (dsavenk@emory.edu)
    Date: 9/11/2013

"""


import settings
from django.core.cache import get_cache
from django.core.exceptions import ObjectDoesNotExist
from abc import abstractmethod

import pickle
import re

import urllib
import urllib2

from ufindit.models import Serp, UserSerpResultsOrder

# Python 2.6 has json built in, 2.5 needs simplejson
try:
    import json
except ImportError:
    import simplejson as json


class SearchResult:
    """
        Represents one web search result
    """
    def __init__(self, url, display_url, title, snippet):
        self._url = url
        self._display_url = display_url
        self._title = title
        self._snippet = snippet

    @property
    def url(self):
        return self._url

    @property
    def safe_url(self):
        return self._url.replace('://','/')

    @property
    def display_url(self):
        return self._display_url

    @property
    def title(self):
        return self._title

    @property
    def snippet(self):
        return self._snippet

    def __unicode__(self):
        return self.title + u'\n' + self.display_url + '\n' + self.snippet


class ResultsSet:
    """
    Represents a collection of results returned by a search engine.
    """
    def __init__(self, query, results):
        self.id = None
        self.query = query
        self.results = results

    def add_result(self, result):
        """
        Adds a search result to the list of results
        """
        assert isinstance(result, SearchResult)
        self.results.add(result)

    def __iter__(self):
        """
        Allows you to iterate over the search results
        """
        for result in self.results:
            yield result

    def __unicode__(self):
        res_str = u''
        rank = 1
        for res in self:
            res_str += unicode(rank) + u'. ' + unicode(res)
            res_str += u'\n'
            rank += 1
        return res_str

    def __len__(self):
        return len(self.results)

    def __getitem__(self, index):
        return self.results[index]


class SearchProvider:
    """
    Abstract class for all search providers.
    """
    @abstractmethod
    def search(self, player, query):
        return None

    @abstractmethod
    def __unicode__(self):
        return ""


class BingSearchProvider(SearchProvider):
    """
        Extracts search results from Bing search engine. Is used inside SearchProxy.
    """
    _api_url_template="https://api.datamarket.azure.com/Bing/Search/Web?"
    _params={"$format":"json",
             "Options":"'EnableHighlighting'"}
    def __init__(self, bing_api_key=settings.BING_API_KEY):
        self._api_key = bing_api_key

    def search(self, player, query, verbose=False):
        BingSearchProvider._params["Query"] = "'" + query + "'"
        url = BingSearchProvider._api_url_template + \
            urllib.urlencode(BingSearchProvider._params)
        req = urllib2.Request(url)
        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, url, '', self._api_key)
        auth_manager = urllib2.HTTPBasicAuthHandler(password_manager)
        opener = urllib2.build_opener(auth_manager)
        urllib2.install_opener(opener)
        handler = urllib2.urlopen(req)
        json_results = handler.read()
        if verbose:
            print json_results
        results = json.loads(json_results)['d']['results']
        return ResultsSet(query, 
            [SearchResult(self.clean(r["Url"]),
                          self.clean(r["DisplayUrl"]),
                          self.clean(r["Title"]),
                          self.clean(r["Description"])) for r in results])

    def clean(self, text):
        """
        Replace some service chars sequences with more appropriate text. E.g.
        \ue000 with <strong>, etc.
        """
        return text.replace(u'\ue000', u'<strong>'). \
                    replace(u'\ue001', u'</strong>')

    def __unicode__(self):
        """
        Returns the name of the search engine. Used for caching.
        """
        return u'BING'


class CacheSearchProvider(SearchProvider):
    """
    Provides caching capabilities for search results.
    """
    def __init__(self, search_provider):
        assert isinstance(search_provider, SearchProvider)
        self._search_provider = search_provider

    def search(self, player, query, verbose=False):
        """
        Checks cache for search results and calls underlining provider if fails.
        """

        # TODO: not good, that I use name of the underlying provider as engine
        results = Serp.objects.filter(query=query, engine=self._search_provider)
        if len(results) == 0:
            if verbose:
                print "Search cache miss"
            results = self._search_provider.search(player, query)
            serp = Serp(query=query, engine=self._search_provider,
                results=pickle.dumps(results))
            serp.save()
            results.id = serp.id
        else:
            if verbose:
                print "Search cache hit"
            serpid = results[0].id
            results = pickle.loads(results[0].results)
            results.id = serpid
        return results

    def __unicode__(self):
        return u'Cache'


class RandomizationSearchProvider(SearchProvider):
    """
    Randomizes search results for the given query
    """
    def __init__(self, search_provider, topn):
        if not isinstance(search_provider, CacheSearchProvider):
            raise ValueError('Randomization can only be used on top of caching')
        self._search_provider = search_provider
        self._topn = topn

    def search(self, player, query, verbose=False):
        results = self._search_provider.search(player, query)
        serp = Serp.objects.get(id = results.id)
        try:
            results_order = UserSerpResultsOrder.objects.get(player=player, serp=serp)
            order = map(int, results_order.order.split(','))
        except ObjectDoesNotExist:
            from random import shuffle
            order = range(len(results))
            # We shuffle only top 10 results
            topn = min((self._topn, len(results)))
            order1 = order[:topn]
            order2 = order[topn:]
            shuffle(order1)
            order = order1 + order2
            results_order = UserSerpResultsOrder(player=player, serp=serp,
                order=",".join(map(str, order)))
            results_order.save()
        results.results = self._shuffle_results(results.results, order)
        return results

    def _shuffle_results(self, results, order):
        res = [None, ] * len(results)
        for index, rank in enumerate(order):
            res[index] = results[rank]
        return res

    def __unicode__(self):
        return u'Randomization'


class SearchProxy(SearchProvider):
    """
    Search engine proxy, used to get search results for a query. Hides actual
    search engine used.
    """
    # The list of supported search engines
    _engines = {"bing":BingSearchProvider}

    @staticmethod
    def get_supported_engines():
        return SearchProxy._engines.keys()

    def __init__(self, engine="bing"):
        self._search_provider = self._get_search_provider(engine)

    def _get_search_provider(self, engine):
        """
        Returns a search engine provider.
        """
        if engine not in SearchProxy._engines:
            raise KeyError("No such engine found: " + engine)
        # Use caching
        provider = CacheSearchProvider(SearchProxy._engines[engine]())
        # Use randomization if setting is on
        if settings.RANDOMIZE_TOPN_RESULTS > 0:
            return RandomizationSearchProvider(provider, settings.RANDOMIZE_TOPN_RESULTS)
        return provider

    def _normalize_query(self, query):
        """
        Normalizes query, the goal is to reduce the number of unique queries.
        """
        return re.sub('\s+', ' ', query).strip().lower()

    def search(self, player, query):
        """
        Returns search results for the given query. Uses search engine specified
        when object was created.
        """
        return self._search_provider.search(player, self._normalize_query(query))

    def __unicode__(self):
        return "Proxy"


if __name__ == "__main__":
    print "This file contains classes to work with search results"
