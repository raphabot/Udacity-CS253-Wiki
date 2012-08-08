import webapp2
import jinja2
import os
import hmac
import re

jinja_env = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)
	
	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)
	
	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))
	
	def setCookie(self, cookie, value):
		self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (cookie, value))
	
	def flushCookie(self, cookie):
		self.response.headers.add_header('Set-Cookie', '%s=; Path=/' % (cookie))
	
	def readCookie(self, cookie):
		return self.request.cookies.get(cookie)
	
	def setHeader(self, header, value):
		self.response.headers[header] = value
	
	def getHash(self, secret, value):
		return hmac.new(secret, value).hexdigest()
	
	def checkHash(self, secret, value1, value2):
		expected_value = self.getHash(secrect, value1)
		given_value = self.getHash(secrect, value2)
		return expected_value == given_value
		
	def valid_username(self, username):
		USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
		if (username != ''):
			return USER_RE.match(username)
	 
	def valid_password(self, password):
		PASSWD_RE = re.compile(r"^.{3,20}$")
		if (password != ''):
			return PASSWD_RE.match(password)

	def valid_email(self, email):
		EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
		if (email != ''):
			return EMAIL_RE.match(email)
	
	#def isLoggedIn(self, )