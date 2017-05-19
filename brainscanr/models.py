# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from django.db import models

# class Question(models.Model):
#     question_text = models.CharField(max_length=200)
#     pub_date = models.DateTimeField('date published')
#
#
# class Choice(models.Model):
#     question = models.ForeignKey(Question, on_delete=models.CASCADE)
#     choice_text = models.CharField(max_length=200)
#     votes = models.IntegerField(default=0)

class Term(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    synonyms = models.TextField()
    acronyms = models.TextField()

    def __str__(self):
        return self.name

    def setsynonyms(self, x):
        self.synonyms = json.dumps(x)

    def getsynonyms(self):
        return json.loads(self.synonyms)

    def setacronyms(self, x):
        self.acronyms = json.dumps(x)

    def getacronyms(self):
        return json.loads(self.acronyms)

class Connection(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    conjunction = models.IntegerField()
    a_not_b = models.IntegerField()
    b_not_a = models.IntegerField()
    disjunction = models.IntegerField()
    prob_association = models.FloatField()

    term_keys = models.TextField()

    def setterm_keys(self, x):
        self.term_keys = json.dumps(x)

    def getterm_keys(self):
        return json.loads(self.term_keys)

class Category(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)		# short no-spaces lowercase name
    title = models.CharField(max_length=255)		# human readable name
    color = models.CharField(max_length=255)		# hex value (no #)
    color_highlight = models.CharField(max_length=255)		# hex value (no #)
    description = models.TextField()	# human readable description of this category

    def __str__(self):
        return self.title
