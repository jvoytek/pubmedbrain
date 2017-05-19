from google.appengine.api import taskqueue

from ../models import Term
from collections import deque
import logging

def chunk(thelist, num):

    list_of_lists = []
    list_of_lists.append([])

    i = 0
    list_num = 0
    for item in thelist:
        list_of_lists[list_num].append(item)

        # increment list counter and reset i
        if i == num - 1:
            list_num += 1
            list_of_lists.append([])
            i = 0
        else:
            i += 1

    return list_of_lists

# Queuing

class Queueing():

    def NewTerms(self, terms, categories):

        list_of_term_lists = chunk(terms, 80)
        list_of_category_lists = chunk(categories, 80)

        for i in range(len(list_of_term_lists)):
            # enqueue this list of terms for addition to the datastore
            taskqueue.add(url='/admin/QueueTermList', params={'terms': list_of_term_lists[i], 'categories': list_of_category_lists[i]})

    def AddSynonyms(self, terms, synonyms):

        list_of_term_lists = chunk(terms, 80)
        list_of_synonym_lists = chunk(synonyms, 80)

        for i in range(len(list_of_term_lists)):
            # enqueue this list of terms and synonyms for addition to the datastore
            taskqueue.add(url='/admin/QueueSynonymList', params={'terms': list_of_term_lists[i], 'synonyms': list_of_synonym_lists[i]})

    def AddAcronyms(self, terms, acronyms):

        list_of_term_lists = chunk(terms, 80)
        list_of_acronym_lists = chunk(acronyms, 80)

        for i in range(len(list_of_term_lists)):
            # enqueue this list of terms and synonyms for addition to the datastore
            taskqueue.add(url='/admin/QueueAddAcronyms', params={'terms': list_of_term_lists[i], 'acronyms': list_of_acronym_lists[i]})

    def UpdateConnections(self):
        offset = 0
        limit = 50

        terms = Term().all().fetch(limit, offset)
        terms_a = deque([])

        # Create a list of all terms
        while len(terms) > 0:
            for term in terms:
                terms_a.append(term.name)
            offset += limit
            terms = Term().all().fetch(limit, offset)

        # Make a copy of the list as terms_b
        terms_b = deque(list(terms_a))

        for term_a in terms_a:
            terms_b_lists = chunk(terms_b, 320)
            for terms_b_list in terms_b_lists:
                taskqueue.add(url='/admin/QueueUpdateConnections', params={'term_a_name': term_a, 'b_terms': terms_b_list})
            terms_b.popleft()

    def UpdateOneTermsConnections(self, term_a):
        # takes term_a's name

        offset = 0
        limit = 50

        terms = Term().all().fetch(limit, offset)
        terms_b = []

        # Create a list of all terms
        while len(terms) > 0:
            for term in terms:
                terms_b.append(term.name)
            offset += limit
            terms = Term().all().fetch(limit, offset)
        terms_b = chunk(terms_b, 100)

        for term_bs in terms_b:
            taskqueue.add(url='/admin/QueueUpdateConnections', params={'term_a_name': term_a, 'b_terms': term_bs})

class QueueAddLower(webapp.RequestHandler):
    def post(self):
        terms = self.request.get_all('terms')

        for term_name in terms:
            term = Term().all().filter('name =', term_name).fetch(1)
            if len(term) > 0:
                term = term[0]
            term_obj = Term();
            term_obj.NameSynonymsAcronymsToLower(term)
            logging.info('Lower: %s' % term_name)

class QueueTermList(webapp.RequestHandler):
    def post(self): # should run at most 1/s
        terms = self.request.get_all('terms')
        categories = self.request.get_all('categories')

        for i in range(len(terms)):
            # enqueue this list of terms for addition to the datastore
            taskqueue.add(url='/admin/QueueNewTerm', params={'name': terms[i], 'category': categories[i]})


class QueueNewTerm(webapp.RequestHandler):
    def post(self): # should run at most 1/s
        name = self.request.get('name')
        category = self.request.get('category')

        logging.info('\nAdding %s (%s)' % (name, category))
        #Create a new term instance
        term = Term()
        term.NewTerm(name, category)


class QueueAddSynonyms(webapp.RequestHandler):
    def post(self): # should run at most 1/s
        name = self.request.get('name')
        synonyms = self.request.get_all('synonyms')

        logging.info('\nAdding synonyms for %s' % name)
        # Get the term instance
        term_obj = Term().all().filter('name =', name).fetch(1)
        term = Term()
        if len(term_obj) > 0:
            term.ReplaceSynonyms(term_obj, synonyms)


class QueueSynonymList(webapp.RequestHandler):
    def post(self): # should run at most 1/s
        terms = self.request.get_all('terms')
        synonyms = self.request.get_all('synonyms')

        for i in range(len(terms)):
            # enqueue this list of terms for addition to the datastore
            taskqueue.add(url='/admin/QueueNewSynonym', params={'name': terms[i], 'synonym': synonyms[i]})

class QueueAddAcronyms(webapp.RequestHandler):
    def post(self): # should run at most 1/s
        terms = self.request.get_all('terms')
        acronyms = self.request.get_all('acronyms')

        for i in range(len(terms)):
            logging.info('\nAdding acronyms for %s' % terms[i])
            # Get the term instance
            term_obj = Term().all().filter('name =', terms[i]).fetch(1)
            term = Term()
            if len(term_obj) > 0:
                term.AddAcronym(term_obj[0], acronyms[i])

class QueueNewSynonym(webapp.RequestHandler):
    def post(self): # should run at most 1/s
        name = self.request.get('name')
        synonym = self.request.get('synonym')

        logging.info('\nAdding synonym "%s" for %s' % (synonym, name))
        # Get the term instance
        term_obj = Term().all().filter('name =', name).fetch(1, 0)
        if len(term_obj) > 0:
            term = Term()
            logging.info('adding synonym')
            term.AddSynonym(term_obj[0], synonym)

class QueueUpdateConnections(webapp.RequestHandler):
    def post(self): # should run at most 1/s
        term_a_name = self.request.get('term_a_name')
        b_terms = self.request.get_all('b_terms')

        for term_b in b_terms:
            if term_a_name != term_b:
                taskqueue.add(url='/admin/QueueUpdateConnection', params={'term_a_name': term_a_name, 'term_b_name': term_b})


class QueueUpdateConnection(webapp.RequestHandler):
    def post(self): # should run at most 1/s
        term_a_name = self.request.get('term_a_name')
        term_b_name = self.request.get('term_b_name')

        logging.info('\nAdding %s x %s' % (term_a_name, term_b_name))
        # get term objects
        term_a_obj = Term().all().filter('name =', term_a_name).fetch(1)
        term_b_obj = Term().all().filter('name =', term_b_name).fetch(1)

        create_connection = True
        if len(term_a_obj) > 0:
            term_a_obj = term_a_obj[0]
        else:
            create_connection = False
        if len(term_b_obj) > 0:
            term_b_obj = term_b_obj[0]
        else:
            create_connection = False

        if create_connection:
            #Create a new connection instance
            connection = Connection()
            connection.UpdateConnection(term_a_obj, term_b_obj)