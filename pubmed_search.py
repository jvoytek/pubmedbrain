#!/usr/bin/env python
# encoding: utf-8
import sys
import os
import re
import urllib
import elementtree.ElementTree as ET
import logging
from django.utils import simplejson

class ExitError(Exception):
    def __init__(self):
        super(ExitError, self).__init__()

def publications(term_a, terms_b):
		 
	search_phrase_a = composeTermSearchPhrase(term_a.name, term_a.synonyms)
	search_phrases = []
	if hasattr(terms_b[0], 'name'):
		for term_b in terms_b:
			search_phrases.append('(%s AND %s)' % (search_phrase_a, composeTermSearchPhrase(term_b.name, term_b.synonyms)))
		search_phrase = ' OR '.join(search_phrases)
	else:
		search_phrase = search_phrase_a
			
	eutils_url = compose_eutils_url(search_phrase, 'jessica.voytek@gmail.com', 'pubmed', 'word', 'uilist', '20', 'y')
	
	page = get_page(eutils_url)
	doc_tree = ET.parse(page)
	count = doc_tree.find('.//Count')	# gets the text value of the first node named "Count"
	
	if count != None:
		query_key = doc_tree.find('.//QueryKey')	# gets the text value of the first node named "QueryKey"
		webenv = doc_tree.find('.//WebEnv')	# gets the text value of the first node named "WebEnv"
		
		efetch_url = compose_efetch_url('20', query_key.text, webenv.text)
		publications = get_page(efetch_url)
		
		json = [{"search_phrase": search_phrase, "results": []}]
		publications = ET.parse(publications)
		publications = publications.findall('.//PubmedArticle')

		for publication in publications:
			title = publication.find('.//ArticleTitle')
			pmid = publication.find('.//PMID')
			abstract = publication.find('.//AbstractText')
			if hasattr(abstract, 'text'):
				abstract = abstract.text
			else:
				abstract = ''
			journal_xml = publication.find('.//Journal')
			journal_title = journal_xml.find('.//Title')
			journal_issue = journal_xml.find('.//JournalIssue')
			journal_pub = journal_issue.find('.//PubDate')
			pub_year = journal_issue.find('.//Year')
			pub_month = journal_issue.find('.//Month')
			pub_day = journal_issue.find('.//Day')
			if pub_year == None:
				pub_year = ""
			else:
				pub_year = pub_year.text

			if pub_month == None:
				pub_month = ""
			else:
				pub_month = pub_month.text

			if pub_day == None:
				pub_day = ""
			else:
				pub_day = pub_day.text
				
			journal = "%s. %s %s %s." % (journal_title.text, pub_year, pub_month, pub_day)
			
			authors_xml = publication.findall('.//Author')
			authors = []
			for author in authors_xml:
				initials = author.find('.//Initials')
				lastname = author.find('.//LastName')
				if not hasattr(initials, 'text'):
					initials = author.find('.//ForeName')
					if not hasattr(initials, 'text'):
						initials = ''
					else:
						initials = initials.text
				else:
					initials = initials.text
				
				if hasattr(lastname, 'text'):
					lastname = lastname.text
				else:
					lastname = ''
					
				authors.append({"initials": initials, "lastname": lastname})
			
			# ignore results that have no title or pubmed id
			if hasattr(title, 'text') and hasattr(pmid, 'text'):
				json[0]['results'].append({"title": title.text, "authors": authors, "journal": journal, "pmid": pmid.text, "abstract": abstract}) 

		return simplejson.dumps(json)
	
def connection(term_a, term_b):

	# concatenate term name and synonyms into search phrase
	term_a_phrase = composeTermSearchPhrase(term_a.name, term_a.synonyms)
	term_b_phrase = composeTermSearchPhrase(term_b.name, term_b.synonyms)
		
	# load default values for connection data
	connection = {'conjunction': 0, 'a_not_b': 0, 'b_not_a': 0 }
	
	# get real valyes of connection data
	connection['conjunction'] = getValue(term_a_phrase, 'AND', term_b_phrase)
	connection['a_not_b'] = getValue(term_a_phrase, 'NOT', term_b_phrase)
	connection['b_not_a'] = getValue(term_b_phrase, 'NOT', term_a_phrase)
	return connection

def composeTermSearchPhrase(name, synonyms):
	term_phrase = '"%s"' % name
	for word in synonyms:
		term_phrase = '%s OR "%s"' % (term_phrase, word)
	term_phrase = '(%s)' % term_phrase
	return term_phrase
				
def getValue(term_1_phrase, conjunction, term_2_phrase):

	search_phrase = '%s %s %s' % (term_1_phrase, conjunction, term_2_phrase)
	url = compose_eutils_url(search_phrase, 'jessica.voytek@gmail.com', 'pubmed', 'word', 'count', '', 'n')
	logging.info(url)
	page = get_page(url)
	doc_tree = ET.parse(page)
	count = doc_tree.find('.//Count')	# gets the text value of the first node named "Count"
	
	if count != None:
		value = int(count.text)		
	else:
		value = 0	
		
	return value


def compose_efetch_url(retmax, query_key, webenv):
		url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&retmax=%s&query_key=%s&WebEnv=%s" % (retmax, query_key, webenv)
		return url

def compose_eutils_url(search_phrase, email, db, field, retype, retmax, usehistory):
	url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=%s&field=%s&term=%s&rettype=%s&email=%s&retmax=%s&usehistory=%s' % (db, field, urllib.quote(search_phrase), retype, email, retmax, usehistory)
	return url
	
def get_page(url):
	"""Returns the HTML for the provided URL"""
	url_opener = urllib.FancyURLopener()
	page = url_opener.open(url)
	return page
