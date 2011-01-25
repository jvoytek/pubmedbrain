#!/usr/bin/env python

#Add a small change
import os
import re
import cgi
import time
import datetime
import itertools
import string
from collections import deque
import urllib
import logging
from django.utils import simplejson

from google.appengine.api.labs import taskqueue
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import pubmed_search
import datamodels

# Page Handlers
class Import(webapp.RequestHandler):
	def get(self):
		current_user = User()
		current_user.getUser()
		# define template variables
		
		offset = 0
		limit = 1000
		

		total_connections = datamodels.ConnectionModel.all(keys_only=True).count()
		total_terms = datamodels.TermModel.all(keys_only=True).count()		
		nickname = current_user.current_user.nickname()
		logout_url = users.create_logout_url('/')

		# Add template variables to list
		template_values = {
			'total_terms': total_terms,
			'total_connections': total_connections,
			'nickname': nickname,
			'logout_url': logout_url
		}

		# Render the page using the template variable list
		path = os.path.join(os.path.dirname(__file__), 'templates', 'import.html')
		self.response.out.write(template.render(path, template_values))

class AddTerm(webapp.RequestHandler):
	def post(self):
		name = self.request.get('name')
		category = self.request.get('category')
		synonyms = self.request.get('synonyms')
		synonyms = string.split(synonyms, ',')
		
		term = Term()
		new_term = term.NewTerm(name, category)
		term.ReplaceSynonyms(new_term, synonyms)
		queue = Queueing()
		queue.UpdateOneTermsConnections(new_term.name)
		
		self.redirect('/admin/Import')

class AddCategory(webapp.RequestHandler):
	def post(self):
		title = self.request.get('title')
		name = self.request.get('name')
		color = self.request.get('color')
		description = self.request.get('description')
		
		category = datamodels.CategoryModel()
		category.title = title		
		category.name = name		
		category.color = color		
		category.description = description
		category.put()				
		
		self.redirect('/admin/Import')

class ImportTerms(webapp.RequestHandler):
	def post(self):
		file_name = self.request.get('terms')
		f = open(file_name, 'r')
		lines = f.readlines()
		
		terms = []
		categories = []
		
		for line in lines:
			line = line.rstrip()
			term_category = string.split(line, ',')
			terms.append(term_category[0])
			categories.append(term_category[1])
				
		queuing = Queueing()
		queuing.NewTerms(terms, categories)
		
		self.redirect('/admin/Import')

class ImportSynonyms(webapp.RequestHandler):
	def post(self):
		file_name = self.request.get('synonyms')
		f = open(file_name, 'r')
		lines = f.readlines()
		
		terms = []
		synonyms = []
		
		for line in lines:
			line = line.rstrip()
			term_synonym = string.split(line, ',')
			terms.append(term_synonym[0])
			synonyms.append(term_synonym[1])
				
		queuing = Queueing()
		queuing.AddSynonyms(terms, synonyms)
		
		self.redirect('/admin/Import')

class UpdateConnections(webapp.RequestHandler):
	def get(self):

		logging.info('Updating Connections!!!')
		queuing = Queueing()
		queuing.UpdateConnections()
		
		self.redirect('/admin/Import')
		

class MainHandler(webapp.RequestHandler):
	def get(self):
		# define template variables
		
		if self.request.get('message') != '':
			message = self.request.get('message')
		else:
			message = False
			
		# Add template variables to list
		terms = Term()
		template_values = terms.GetTerms('all')
		template_values['message'] = message

		# Render the page using the template variable list
		path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
		self.response.out.write(template.render(path, template_values))

	def post(self):
		body = self.request.get('body')
		first_name = self.request.get('first_name')
		last_name = self.request.get('last_name')
		email = self.request.get('email')
		
		message = datamodels.MessageModel()
		
		message.body = body
		message.first_name = first_name
		message.last_name = last_name
		message.from_email = email
		
		message.put()
		
		self.redirect('/?message=<span class="confirm">Thank you for your message!</span>')
		

class Search(webapp.RequestHandler):
	def get(self):

		# define template variables
						
		terms = Term()
		template_values = terms.GetTerms('all')
		
		if self.request.get('term_a') != '':
			term_a_name = self.request.get('term_a')
		else:
			term_a_name = template_values['categories'][4]['terms'][0].name

		term_a = datamodels.TermModel.all().filter('name_lower =', term_a_name.lower()).fetch(1)
		if len(term_a) == 0:
			term_a = datamodels.TermModel.all().filter('synonyms_lower =', term_a_name.lower()).fetch(1)
			if len(term_a) == 0:
				term_a = datamodels.TermModel.all().filter('acronyms_lower =', term_a_name.lower()).fetch(1)
			
		
		if len(term_a) > 0:
			term_a[0].color = getColor(term_a[0].category)
			
			terms_c = []
			
			i = 0
			calcStart = datetime.datetime.now()
			message = ''
		else:
			term_a = ['']
			message = 'Sorry, "%s" was not found. <a href="/Terms">Click here for a list of available terms</a>' % term_a_name
		
		# Add template variables to list
		template_values['message'] = message
		template_values['search_term'] = term_a_name
		template_values['term_a'] = term_a[0]
		logging.info('\n%s' % template_values)
		
		# Render the page using the template variable list
		path = os.path.join(os.path.dirname(__file__), 'templates', 'search.html')
		self.response.out.write(template.render(path, template_values))

class ListOfTerms(webapp.RequestHandler):
	def get(self):
		# define template variables
		
		if self.request.get('message') != '':
			message = self.request.get('message')
		else:
			message = False
			
		# define template variables
						
		terms = Term()
		template_values = terms.GetTerms('all')
		

		# Add template variables to list
		template_values['message'] = message

		# Render the page using the template variable list
		path = os.path.join(os.path.dirname(__file__), 'templates', 'terms.html')
		self.response.out.write(template.render(path, template_values))

	def post(self):
		term = self.request.get('term')
		body = self.request.get('body')
		first_name = self.request.get('first_name')
		last_name = self.request.get('last_name')
		email = self.request.get('email')
		
		message = datamodels.MessageModel()
		
		message.term = term
		message.body = body
		message.first_name = first_name
		message.last_name = last_name
		message.from_email = email
		
		message.put()
		
		self.redirect('/Terms?message=<span class="confirm">Thank you for your suggestion!</span>')

class Paper(webapp.RequestHandler):
	def get(self):
		# define template variables
		
		if self.request.get('message') != '':
			message = self.request.get('message')
		else:
			message = False

		# define template variables
						
		terms = Term()
		template_values = terms.GetTerms('all')
			
		# Add template variables to list
		template_values['message'] = message

		# Render the page using the template variable list
		path = os.path.join(os.path.dirname(__file__), 'templates', 'paper.html')
		self.response.out.write(template.render(path, template_values))


class Request(webapp.RequestHandler):
	def post(self):
		
		request_type = self.request.get('request_type')
		# request types include
			# esearch - returns publications from pubmed (JSON) with a term_a and a term_b
			# circ_connections - returns JSON formatted connections based on a term_a		
			# circ_connection_data - returns JSON of connection data for the max_results
			# tree_data - returns JSON formatted connections based on a term_a		
	
		#
		# esearch - returns publications from pubmed (JSON) with a term_a and a term_b
		#
	
		if request_type == 'esearch':
			term_a_name = urllib.unquote(self.request.get('term_a'))
			terms_b_names = urllib.unquote(self.request.get('term_b'))
			terms_b_names = string.split(terms_b_names, ',')
			
			term_a = datamodels.TermModel.all().filter('name =', term_a_name).fetch(1)
			terms_b = []
			
			for term_b_name in terms_b_names:
				term_b = datamodels.TermModel.all().filter('name =', term_b_name).fetch(1)
				if len(term_b) > 0:
					term_b = term_b[0]
				terms_b.append(term_b)
			
			if len(term_a) > 0:
				term_a = term_a[0]
				
				publication_json = pubmed_search.publications(term_a, terms_b)
				
				self.response.out.write(publication_json)
		
		#
		# connections - returns JSON formatted connections based on a term_a
		#
		
		elif request_type == 'circ_connections':
				
			max_results = int(self.request.get('max_results'))
			
						
			terms = Term()
			template_values = terms.GetTerms('all')
			
			# get term_a data model object
			if self.request.get('term_a') != '':
				term_a_name = urllib.unquote(self.request.get('term_a'))
			else:
				term_a_name = template_values['categories'][4]['terms'][0].name
	
			term_a = datamodels.TermModel.all().filter('name_lower =', term_a_name.lower()).fetch(1)
			if len(term_a) == 0:
				term_a = datamodels.TermModel.all().filter('synonyms_lower =', term_a_name.lower()).fetch(1)
				if len(term_a) == 0:
					term_a = datamodels.TermModel.all().filter('acronyms_lower =', term_a_name.lower()).fetch(1)
			
			if len(term_a) > 0:
				# get connections
				connections = datamodels.ConnectionModel.all().filter('term_keys =', term_a[0].key()).filter('prob_association >', 0.0).order('-prob_association').fetch(max_results)
				
				term_a[0].color = getColor(term_a[0].category)
				terms_c = []
				i = 0
				calcStart = datetime.datetime.now()
				
				connection_json = [{'id': term_a[0].name, 'name': term_a[0].name, 'data': {'$dim': 25, '$color': term_a[0].color, 'category': term_a[0].category, 'prob_association': '1', '$type': 'star'}, 'adjacencies': []}]
				
				for connection in connections:
					term_keys = list(connection.term_keys)
					term_keys.remove(term_a[0].key())
					term_b = datamodels.TermModel.all().filter('__key__ =', term_keys[0]).fetch(1)
					if len(term_b) > 0:
						term_b = term_b[0]
					
					
					connection.connections = []	
					if connections[0].prob_association > 0:
						connection.weight = ((connection.prob_association / connections[0].prob_association) * 4) + 1
						connection.alpha = (connection.prob_association / connections[0].prob_association) + .2
					else:
						connection.weight = 1
						connection.alpha = 1
						

					# find connection from term_b to to other term_b's
					terms_c.append(term_b)

					for term_c in terms_c:
						if term_c.name != term_b.name:
							connection_c = datamodels.ConnectionModel.all().filter('term_keys =', term_c.key()).filter('term_keys =', term_b.key()).fetch(1)
							if len(connection_c) > 0:
								if connections[0].prob_association > 0:
									connection_c[0].weight = ((connection_c[0].prob_association / connections[0].prob_association) * 4) + 1
									if connection_c[0].weight > 5:
										connection_c[0].weight = 5
										
									connection_c[0].name = term_c.name
									connection_c[0].alpha = (connection_c[0].prob_association / connections[0].prob_association) + .2
								else:
									connection_c[0].weight = 1
									connection_c[0].name = term_c.name
									connection_c[0].alpha = .2

								connection.connections.append({'nodeTo': connection_c[0].name, 'data': {'$lineWidth': connection_c[0].weight, '$alpha': connection_c[0].alpha, '$color': '#CCCCCC'}})
					i += 1
						
					# add data to connection json
					connection_json[0]['adjacencies'].append({'nodeTo': term_b.name, 'data': {'$lineWidth': connection.weight, 'name': term_b.name, '$alpha': connection.alpha}})
					
					connection_json.append({'id': term_b.name, 'name': term_b.name, 'data': {'$dim': 10, '$color': getColor(term_b.category), 'category': term_b.category, 'prob_association': round(connection.prob_association, 4)}, 'adjacencies': connection.connections })

				logging.info("calcTime: %s", (datetime.datetime.now() - calcStart))
				message = ''
						
			
			# Render and Return JSON to requesting script
			self.response.out.write(simplejson.dumps(connection_json))


		#
		# connection_data - returns JSON of connection data for the max_results
		#
		elif request_type == 'circ_connection_data':
			max_results = int(self.request.get('max_results'))
			
						
			terms = Term()
			template_values = terms.GetTerms('all')
			
			# get term_a data model object
			if self.request.get('term_a') != '':
				term_a_name = urllib.unquote(self.request.get('term_a'))
			else:
				term_a_name = template_values['categories'][4]['terms'][0].name
	
			term_a = datamodels.TermModel.all().filter('name_lower =', term_a_name.lower()).fetch(1)
			if len(term_a) == 0:
				term_a = datamodels.TermModel.all().filter('synonyms_lower =', term_a_name.lower()).fetch(1)
				if len(term_a) == 0:
					term_a = datamodels.TermModel.all().filter('acronyms_lower =', term_a_name.lower()).fetch(1)
			
			if len(term_a) > 0:
				# get connections
				connections = datamodels.ConnectionModel.all().filter('term_keys =', term_a[0].key()).filter('prob_association >', 0.0).order('-prob_association').fetch(max_results)
				
				i = 0
				calcStart = datetime.datetime.now()
				
				connection_json = []
				
				for connection in connections:
					term_keys = list(connection.term_keys)
					term_keys.remove(term_a[0].key())
					term_b = datamodels.TermModel.all().filter('__key__ =', term_keys[0]).fetch(1)
					if len(term_b) > 0:
						term_b = term_b[0]
					
					if term_a[0].category != 'silly' and term_b.category != 'silly':
						connection_json.append({'term_b': term_b.name, 'conjunction': connection.conjunction, 'disjunction': connection.disjunction, 'prob_association': connection.prob_association})
					elif term_a[0].category == 'silly':
						connection_json.append({'term_b': term_b.name, 'conjunction': connection.conjunction, 'disjunction': connection.disjunction, 'prob_association': connection.prob_association})
				
						
			# Render and Return JSON to requesting script
			self.response.out.write(simplejson.dumps(connection_json))

		#
		# tree_connections - returns JSON of connections for tree
		#
		elif request_type == 'tree_connections':
			max_results = 4
			levels = 3
			terms = Term()
			template_values = terms.GetTerms('all')
			
			# get term_a data model object
			if self.request.get('term_a') != '':
				term_a_name = urllib.unquote(self.request.get('term_a'))
			else:
				term_a_name = template_values['categories'][4]['terms'][0].name
	
			term_a = datamodels.TermModel.all().filter('name_lower =', term_a_name.lower()).fetch(1)
			if len(term_a) == 0:
				term_a = datamodels.TermModel.all().filter('synonyms_lower =', term_a_name.lower()).fetch(1)
				if len(term_a) == 0:
					term_a = datamodels.TermModel.all().filter('acronyms_lower =', term_a_name.lower()).fetch(1)
			
			if len(term_a) > 0:
				# get connections
				
				
				term_a[0].color = getColor(term_a[0].category)
				calcStart = datetime.datetime.now()
				
				connection_json = [{'id': '%s_root' % term_a[0].name, 'name': term_a[0].name, 'data': {'$color': '#%s' % term_a[0].color, 'category': term_a[0].category, 'prob_association': 1}, 'children': []}]
				
				getConnections(0, levels, term_a[0].key(), connection_json[0]['children'], max_results)
								
				logging.info("calcTime: %s", (datetime.datetime.now() - calcStart))
				message = ''
						
			
			# Render and Return JSON to requesting script
			self.response.out.write(simplejson.dumps(connection_json))

COUNTER = 0

def getConnections(i, levels, term_key, children_list_obj, max_results):
	connections = datamodels.ConnectionModel.all().filter('term_keys =', term_key).filter('prob_association >', 0.0).order('-prob_association').fetch(max_results)
	for connection in connections:
		term_keys = list(connection.term_keys)
		term_keys.remove(term_key)
		term_b = datamodels.TermModel.all().filter('__key__ =', term_keys[0]).fetch(1)
		if len(term_b) > 0:
			term_b = term_b[0]
																
		# add data to connection json
		global COUNTER 
		COUNTER += 1
		node = {'id': '%s_%s' % (term_b.name, COUNTER), 'name': term_b.name, 'data': {'$color': getColor(term_b.category), 'category': term_b.category, 'prob_association': round(connection.prob_association, 4)}, 'children': []}
		children_list_obj.append(node)
		if i < levels:
			j = i + 1
			getConnections(j, levels, term_b.key(), node['children'], max_results)
	
	i += 1

class AddLower(webapp.RequestHandler):
	def post(self):
		
		offset = 0
		limit = 50
		
		terms = datamodels.TermModel().all().fetch(limit, offset)
		terms_a = deque([])
		
		# Create a list of all terms
		while len(terms) > 0:			
			for term in terms:
				terms_a.append(term.name)
			offset += limit
			terms = datamodels.TermModel().all().fetch(limit, offset)
				
			terms_a_lists = chunk(terms_a, 320)
			for terms_a_list in terms_a_lists:
				taskqueue.add(url='/admin/QueueAddLower', params={'terms': terms_a_list})
			terms_a.popleft()

		self.redirect('/admin/Import')

class ImportAcronyms(webapp.RequestHandler):
	def post(self):
		file_name = self.request.get('acronyms')
		f = open(file_name, 'r')
		lines = f.readlines()
		
		terms = []
		acronyms = []
		
		for line in lines:
			line = line.rstrip()
			term_acronym = string.split(line, ',')
			terms.append(term_acronym[0])
			acronyms.append(term_acronym[1])
				
		queuing = Queueing()
		queuing.AddAcronyms(terms, acronyms)
		
		self.redirect('/admin/Import')
	
# Helpers

class User():
	current_user = None
	user_data = None

	def __init__(self):
		self.current_user = users.get_current_user()
		self.user_data = None
			
		# Get the user's data
		self.getUser()
		
		# If the user doesn't already exist, create it
		if self.user_data == None:
			self.addUser()
						
	def addUser(self):
		new_user = datamodels.UserModel()
		new_user.user = self.current_user
		new_user.id = self.current_user.user_id()
		new_user.put()
		self.user_data = new_user
	
	def getUser(self):
		# Get the user's data
		user_query = datamodels.UserModel.all().filter("id =", self.current_user.user_id())
		self.user_data = user_query.get()
		
	#def deleteUser(self):
	

class Term():

	def NewTerm(self, name, category):
		
		term = datamodels.TermModel().all().filter('name =', name).fetch(1, 0)
		
		if len(term) == 0:
			term = datamodels.TermModel()
			term.name = name
			term.name_lower = name.lower()
			term.category = category
			term.put()
		else:
			term = term[0]
			
		return term
		
	def ReplaceSynonyms(self, term, synonyms):
		
		term.synonyms = synonyms
		term.synonyms_lower = [x.lower() for x in synonyms]
		term.put()
		
		return term

	def AddSynonym(self, term, synonym):
		
		if synonym not in term.synonyms:
			term.synonyms.append(synonym)
			term.synonyms_lower.append(synonym.lower())
			term.put()
		
		return term

	def ReplaceAcronyms(self, term, acronyms):
		
		term.acronyms = acronyms
		term.acronyms_lower = [x.lower() for x in acronyms]
		term.put()
		
		return term

	def AddAcronym(self, term, acronym):
		
		if acronym not in term.acronyms:
			term.acronyms.append(acronym)
			term.acronyms_lower.append(acronym.lower())
			term.put()
		
		return term
	
	def NameSynonymsAcronymsToLower(self, term):
		
		term.name_lower = term.name.lower()
		term.synonyms_lower = [x.lower() for x in term.synonyms]
		term.acronyms_lower = [x.lower() for x in term.acronyms]
		term.put()
		
		return term
	
	def GetTerms(self, category):
		
		if category == 'all':
		
			categories = datamodels.CategoryModel.all().order('title')
					
			values = []
			
			for category in categories:
				terms = datamodels.TermModel.all().filter('category =', category.name).order('name').fetch(1000)
				values.append(dict([('name', category.name), ('terms', terms), ('title', category.title), ('color', category.color)]))
			
			return {'categories': values}

class Connection():
	
	def NewConnection(self, term_a, term_b):
		
		connection = datamodels.ConnectionModel().all().filter('term_keys =', term_a.key()).filter('term_keys =', term_b.key()).fetch(1)
		if len(connection) > 0:
			connection = connection[0]
		else:
			# term_a and term_b must be datastore objects
			connection = datamodels.ConnectionModel()
			connection.term_keys = [term_a.key(), term_b.key()]
			connection.put()
		
		return connection
		
	def UpdateConnection(self, term_a, term_b):
		# term_a and term_b must be datastore objects
		
		# get the connection based on term_a and term_b's keys
		connection = datamodels.ConnectionModel().all().filter('term_keys =', term_a.key()).filter('term_keys =', term_b.key()).fetch(1)
		if len(connection) > 0:
			connection = connection[0]
		else:
			connection = self.NewConnection(term_a, term_b)
		
		# if the data hasn't been modified in more than 24 hours OR the connection was created in the last 24 hours
		if (datetime.datetime.now() - connection.modified) > datetime.timedelta(hours = 24) or (datetime.datetime.now() - connection.created) < datetime.timedelta(hours = 24):	
			# get the data from pubmed
			# requires term_a and term_b as datastore objects
			connection_data = pubmed_search.connection(term_a, term_b)
			
			# add the data to the datamodel
			connection.conjunction = connection_data['conjunction']
			connection.a_not_b = connection_data['a_not_b']
			connection.b_not_a = connection_data['b_not_a']
			
			# calculate disjunction and probability of association
			connection.disjunction = connection_data['a_not_b'] + connection_data['b_not_a']
			if (float(connection_data['a_not_b'] + connection_data['b_not_a']) != 0):
				connection.prob_association = float(connection_data['conjunction']) / float((connection_data['a_not_b'] + connection_data['b_not_a']))
			else:
				connection.prob_association = 0.0
			
			# save the data		
			connection.put()

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
		
		terms = datamodels.TermModel().all().fetch(limit, offset)
		terms_a = deque([])
		
		# Create a list of all terms
		while len(terms) > 0:			
			for term in terms:
				terms_a.append(term.name)
			offset += limit
			terms = datamodels.TermModel().all().fetch(limit, offset)
		
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
		
		terms = datamodels.TermModel().all().fetch(limit, offset)
		terms_b = []
		
		# Create a list of all terms
		while len(terms) > 0:			
			for term in terms:
				terms_b.append(term.name)
			offset += limit
			terms = datamodels.TermModel().all().fetch(limit, offset)
		terms_b = chunk(terms_b, 100)
		
		for term_bs in terms_b:		
			taskqueue.add(url='/admin/QueueUpdateConnections', params={'term_a_name': term_a, 'b_terms': term_bs})
										

class QueueAddLower(webapp.RequestHandler):
	def post(self):
		terms = self.request.get_all('terms')
		
		for term_name in terms:
			term = datamodels.TermModel().all().filter('name =', term_name).fetch(1)
			if len(term) > 0:
				term = term[0]
			term_obj = Term();
			term_obj.NameSynonymsToLower(term)
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
		term_obj = datamodels.TermModel().all().filter('name =', name).fetch(1)
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
			term_obj = datamodels.TermModel().all().filter('name =', terms[i]).fetch(1)
			term = Term()
			if len(term_obj) > 0:
				term.AddAcronym(term_obj[0], acronyms[i])
			        
class QueueNewSynonym(webapp.RequestHandler):
	def post(self): # should run at most 1/s
		name = self.request.get('name')
		synonym = self.request.get('synonym')
		
		logging.info('\nAdding synonym "%s" for %s' % (synonym, name))
		# Get the term instance
		term_obj = datamodels.TermModel().all().filter('name =', name).fetch(1, 0)
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
		term_a_obj = datamodels.TermModel().all().filter('name =', term_a_name).fetch(1)
		term_b_obj = datamodels.TermModel().all().filter('name =', term_b_name).fetch(1)
		
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
			        
	
class ExportData(webapp.RequestHandler):
	def get(self):
		offset = 0
		limit = 500
		
		self.response.out.write('Term A,Term B,conjunction,A~B,B~A,disjunction,conj/disj\n')
		
		for i in range(12):
			connections = datamodels.ConnectionModel().all().fetch(limit, offset)
			for connection in connections:
				self.response.out.write('%s,%s,%s,%s,%s,%s,%s\n' % (connection.term_a, connection.term_b, connection.conjunction, connection.a_not_b, connection.b_not_a, connection.disjunction, connection.connectivity))
			offset += limit
				
					
		
# Usefull functions

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

def test_page(self, message):
	# Add template variables to list
	template_values = {
		'message': message,
	}

	# Render the page using the template variable list
	path = os.path.join(os.path.dirname(__file__), 'templates', 'message.html')
	self.response.out.write(template.render(path, template_values))

def getColor(cat):
	
	category = datamodels.CategoryModel.all().filter('name =', cat).fetch(1)
	if len(category) > 0:
		category = category[0]
		return '#%s' % category.color
	else:
		return '#333333'		
		
	        
def main():
	application = webapp.WSGIApplication([
		('/', MainHandler),
		('/Search', Search),
		('/Terms', ListOfTerms),
		('/Paper', Paper),
		('/request', Request),
		('/admin/QueueAddLower', QueueAddLower),
		('/admin/AddLower', AddLower),
		('/admin/AddCategory', AddCategory),
		('/admin/Import', Import),
		('/admin/ImportTerms', ImportTerms),
		('/admin/ImportSynonyms', ImportSynonyms),
		('/admin/ImportAcronyms', ImportAcronyms),
		('/admin/AddTerm', AddTerm),
		('/admin/UpdateConnections', UpdateConnections),
		('/admin/QueueTermList', QueueTermList),
		('/admin/QueueSynonymList', QueueSynonymList),
		('/admin/QueueAddAcronyms', QueueAddAcronyms),
		('/admin/QueueNewTerm', QueueNewTerm),
		('/admin/QueueNewSynonym', QueueNewSynonym),
		('/admin/QueueUpdateConnection', QueueUpdateConnection),
		('/admin/QueueUpdateConnections', QueueUpdateConnections),
		('/admin/ExportData', ExportData)
		],debug=True)
	run_wsgi_app(application)

if __name__ == "__main__":
    main()
