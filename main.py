import webapp2
import jinja2
import os
import hmac
import utils
from google.appengine.ext import db
from google.appengine.api import memcache
from operator import itemgetter, attrgetter


SECRET = "SuperMasterSecret"

#Models
class BlogUser(db.Model):
	username = db.StringProperty(required = True)
	hash_password = db.StringProperty(required = True)
	email = db.EmailProperty()
	
class WikiPage(db.Model):
	title = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)

#
class Signup(utils.Handler):
	def signup_page(self, username="", user_err ="",password="", password_err="", verify="", verify_err="", email="", email_err=""):
		self.render("signup.html", username=username, user_err =user_err,password=password, password_err=password_err, verify=verify, verify_err=verify_err, email=email, email_err=email_err)
	
	def checaDados(self, username, password, verify, email):
		user_err = ""
		verify_err = ""
		email_err = ""
		password_err = ""
		users = memcache.get('users')
		if (users == None):
			users = BlogUser.all()
			users = list(users)
			memcache.set('users',users)
		if (not self.valid_username(username)):
			user_err = "Invalid Username!"
		for user in users:
			if user.username == username:
				user_err = "Username already taken!"
		if (not self.valid_password(password)):
			password_err = "Invalid Password!"
			password = ""
			verify = ""
		else:
			if (not password == verify):
				verify_err = "Passwords don't match"
				password = ""
				verify = ""
		if (not self.valid_email(email)):
			if (email != ''):
				email_err = "Invalid Email!"
		if (user_err or password_err or verify_err or email_err):
			self.signup_page(username, user_err, password, password_err, verify, verify_err, email, email_err)
		else:
			hash_password = self.getHash(SECRET, password)
			if not(email == ""):
				user = BlogUser(username = username, hash_password = hash_password, email = email)
			else:
				user = BlogUser(username = username, hash_password = hash_password)
			user_key = user.put()
			users.append(user)
			memcache.set('users',users)
			self.setCookie('user_id=', str(user.key().id())+'|'+str(hash_password))
			self.redirect('/')
			
	def get(self):
		self.signup_page()
		
	def post(self):
		self.checaDados(self.request.get('username'),self.request.get('password'),self.request.get('verify'),self.request.get('email'))

class Login(utils.Handler):
	def loginpage(self, username="", password="", error=""):
		self.render("login.html", username=username, password=password, error=error)
		
	def get(self):
		self.loginpage()
		
	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		error = ""
		user = ""
		users = memcache.get("users")
		if (users == None):
			users = BlogUser.all()
			memcache.set("users", users)
		for u in users:
			if (u.username == username):
				user = u
		hash_password = self.getHash(SECRET, password)
		if (not password) or (not username) or (user == '') or (hash_password != user.hash_password):
			error = "username or password invalid"
			self.loginpage(username=username, error=error)
		else:
			self.setCookie('user_id', str(user.key().id())+'|'+str(hash_password))
			self.redirect('/')

class Logout(utils.Handler):
	def get(self):
		self.flushCookie('user_id')
		self.redirect('/')

class ShowPage(utils.Handler):
	def get(self, page_title):
		page_title = page_title[1:]
		if page_title == '':
			page_title = 'index'
		pages = memcache.get('pages')
		if (pages == None):
			pages = WikiPage.all()
			pages = list(pages)
			memcache.set('pages',pages)
		page = ''
		for p in pages:
			if p.title == page_title:
				page = p
		if page:
			self.render('page.html', page = page)
		else:
			self.redirect('/_edit/'+page_title)
		
class EditPage(utils.Handler):
	def post(self, page_title):
		title = page_title[1:]
		if title == '':
			title = 'index'
		content = self.request.get('content')
		page = WikiPage(title = title, content = content)
		#Atualiza o mais novo na lista de paginas
		pages = memcache.get('pages')
		if (pages == None):
			pages = WikiPage.all
			pages = list(pages)
		pages.append(page)
		memcache.set('pages',pages)
		#Atualiza o historico
		history = memcache.get(title)
		if (history == None):
			history = db.GqlQuery('SELECT * FROM WikiPage WHERE title = :1 ORDER BY created ASC', page_title)
			history = list(history)
		history.insert(0,page)
		memcache.set(title, history)
		#Insere no bd
		page.put()
		self.redirect(page_title)
		
	def get(self, page_title):
		page_title = page_title[1:]
		if page_title == '':
			page_title = 'index'
		pages = memcache.get('pages')
		if (pages == None):
			pages = WikiPage.all()
			pages = list(pages)
			memcache.set('pages',pages)
		page = None
		for p in pages:
			if p.title == page_title:
				page = p
		if page == None:
			page = WikiPage(title = page_title, content = 'Enter the new content in here')
		self.render('edit.html', page = page)
		
class HistoryPage(utils.Handler):
	def get(self, page_title):
		page_title = page_title[1:]
		if page_title == '':
			page_title = 'index'
		pages = memcache.get(page_title)
		if (pages == None):
			pages = db.GqlQuery('SELECT * FROM WikiPage WHERE title = :1 ORDER BY created DESC', page_title)
			pages = list(pages)
			memcache.set(page_title, pages)
		self.render('history.html', pages = pages, title = page_title)

        

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([('/signup', Signup),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/_edit' + PAGE_RE, EditPage),
                               ('/_history' + PAGE_RE, HistoryPage),
                               (PAGE_RE, ShowPage)
                               ],
                              debug=True)