# coding:utf-8

from jupyterhub.auth import Authenticator
from tornado import gen

from mysqlauthenticator.DAO.base import init
from mysqlauthenticator.DAO.user import User

import os

class MysqlAuthenticator(Authenticator):

	"""JupyterHub Authenticator Based on Mysql"""

	def __init__(self, **kwargs):
		super(MysqlAuthenticator, self).__init__(**kwargs)

	@gen.coroutine
	def authenticate(self, handler, data):
		mysql_host = os.environ["JUPYTER_MYSQL_SERVICE_HOST"]
		mysql_port = os.environ["JUPYTER_MYSQL_SERVICE_PORT"]
		db_url = "mysql+mysqlconnector://root:root@"+mysql_host+":"+mysql_port+"/jupyterhub"
		session = init(db_url)

		username = data['username']
		passwd = data['password']

		try:
			user = session.query(User).filter(User.username == username).filter(User.password == passwd).one()
			if user is not None:
				print("okok")
				return user.username
			else:
				print("none")
				return None
		except:
			print("something wrong")
			return None


