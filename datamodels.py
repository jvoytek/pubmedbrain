#!/usr/bin/env python

from google.appengine.ext import db

# Data Models
class UserModel(db.Model):
	id = db.StringProperty()
	user = db.UserProperty()
	created = db.DateTimeProperty(auto_now_add=True)

class TermModel(db.Model):
	created = db.DateTimeProperty(auto_now_add=True)
	name = db.StringProperty()
	name_lower = db.StringProperty()
	category = db.StringProperty()
	synonyms = db.StringListProperty()
	synonyms_lower = db.StringListProperty()
	acronyms = db.StringListProperty()
	acronyms_lower = db.StringListProperty()
	
class ConnectionModel(db.Model):
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)
	term_keys = db.ListProperty(db.Key)	# Limit 1MB of data
	conjunction = db.IntegerProperty()
	a_not_b = db.IntegerProperty()
	b_not_a = db.IntegerProperty()
	disjunction = db.IntegerProperty()
	prob_association = db.FloatProperty()

class MessageModel(db.Model):
	created = db.DateTimeProperty(auto_now_add=True)
	first_name = db.StringProperty()
	last_name = db.StringProperty()
	from_email = db.StringProperty()
	term = db.StringProperty(multiline=True)
	body = db.TextProperty()

class CategoryModel(db.Model):
	created = db.DateTimeProperty(auto_now_add=True)
	name = db.StringProperty()		# short no-spaces lowercase name
	title = db.StringProperty()		# human readable name
	color = db.StringProperty()		# hex value (no #)
	color_highlight = db.StringProperty()		# hex value (no #)
	description = db.TextProperty()	# human readable description of this category
	
