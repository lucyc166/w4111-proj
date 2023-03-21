
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
	python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


# XXX: The URI should be in the format of: postgresql://USER:PASSWORD@34.73.36.248/project1

DATABASE_USERNAME = "apl2171"
DATABASE_PASSWRD = "5567"
DATABASE_HOST = "34.148.107.47" # change to 34.28.53.86 if you used database 2 for part 2
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/project1"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
with engine.connect() as conn:
	create_table_command = """
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	"""
	res = conn.execute(text(create_table_command))
	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	conn.commit()


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#

# global variables to track logged in user
user_id = ""
email = ""

@app.route('/')
def index():
	return render_template("index.html")

@app.route('/login')
def login():
	return render_template("login.html")

@app.route('/hub')
def hub():
	print(user_id)

	#grabbing list of orgs affiliated with user
	select_query = "SELECT * FROM organizations o JOIN affiliated_with aw ON aw.org_id = o.org_id WHERE user_id = '%s'" % (user_id)
	cursor = g.conn.execute(text(select_query))
	print(select_query)
	orgs = []
	for result in cursor:
		orgs.append(result)
	print(orgs)
	return render_template("hub.html", orgs = orgs, user_id = user_id, email = email)

# url routing for custom org page
@app.route('/org/<org_id>')
def profile(org_id):

	# grab org info from sql query
	select_query = "SELECT * FROM organizations WHERE org_id = '%s'" % (org_id)
	cursor = g.conn.execute(text(select_query))
	print(select_query)
	orgs = []
	for result in cursor:
		orgs.append(result)
	print(orgs)

	# grab users affiliated with org from query
	select_query = "SELECT u.user_id, u.user_email, u.password  FROM organizations o JOIN affiliated_with aw ON aw.org_id = o.org_id JOIN users u on aw.user_id = u.user_id WHERE o.org_id = '%s'" % (org_id)
	cursor = g.conn.execute(text(select_query))
	print(select_query)
	users = []
	for result in cursor:
		users.append(result)
	print(result)	
	return render_template("org_profile.html", orgs = orgs, users = users)

@app.route('/org/<event_id>')

@app.route('/login_submit', methods =["GET", "POST"])
def login_submit():
	if request.method == "POST":
		global email

		# grab email and password from log in form
		email = request.form.get("email")
		password = request.form.get("password")
		
		# check if email and password are in the database
		select_query = "SELECT user_id FROM users WHERE user_email = '%s' AND password = '%s'" % (email, password)
		cursor = g.conn.execute(text(select_query))

		# if empty query (no match), refresh login page with error
		if cursor.rowcount == 0: # empty query 
			return render_template("login.html", access = "The email or password was incorrect. Please try again.")
		
		# otherwise, show a custom user hub page
		else:
			global user_id
			user_id = cursor.fetchone()[0]
			print(user_id)
			return redirect('/hub')
			#return render_template("hub.html", email = email, user_id = user_id)
			## ** FIGURE HOW TO REROUTE THIS TO APP.ROUTE (HUB) so the org queries show up

@app.route('/admin')
def admin():
	# DEBUG: this is debugging code to see what request looks like
	print(request.args)

	# query orgs
	select_query = "SELECT * FROM organizations"
	cursor = g.conn.execute(text(select_query))
	orgs = []
	for result in cursor:
		orgs.append(result)

	# query users
	select_query = "SELECT * FROM users"
	cursor = g.conn.execute(text(select_query))
	users = []
	for result in cursor:
		users.append(result)

	cursor.close()
	return render_template("admin.html", orgs = orgs, users = users)

# add org form
@app.route('/add_org', methods=["GET", "POST"])
def add_org():
	# accessing form inputs from user
	org_name = request.form.get("org_name")
	org_desc = request.form.get("org_desc")
	org_email = request.form.get("org_email")
	marketing_email = request.form.get("marketing_email")
	comms_email = request.form.get("comms_email")
	finance_email = request.form.get("finance_email")
	advisor_email = request.form.get("advisor_email")
	'''
	org_info = []
	org_info.extend[org_name, org_desc, org_email, marketing_email, comms_email, finance_email, advisor_email]
	for i in range(len(org_info)):
		if org_info[i] == "":
			org_info[i] = null
   '''

	# new org_id is highest org_id + 1
	select_query = "SELECT max(org_id) FROM organizations"
	cursor = g.conn.execute(text(select_query))
	org_id = str(int(cursor.fetchone()[0]) + 1).zfill(4) # fill with leading 0's [0001, 0002]

	# query to add org to organizations table
	select_query = "INSERT INTO organizations (org_id, org_name, org_description, org_email, marketing_email, comms_email, finance_email, advisor_email) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (org_id, org_name, org_desc, org_email, marketing_email, comms_email, finance_email, advisor_email)
	print(select_query)
	g.conn.execute(text(select_query))
	g.conn.commit()

	# query to add affiliated_with linking logged in user w/ org
	select_query = "INSERT INTO affiliated_with (user_id, org_id) VALUES ('%s', '%s')" % (user_id, org_id)
	print(select_query)
	g.conn.execute(text(select_query))
	g.conn.commit()

	return redirect('/hub')

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
	# accessing form inputs from user
	name = request.form['name']
	
	# passing params in for each variable into query
	params = {}
	params["new_name"] = name
	g.conn.execute(text('INSERT INTO test(name) VALUES (:new_name)'), params)
	g.conn.commit()
	return redirect('/')



if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
