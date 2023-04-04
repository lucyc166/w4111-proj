
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
from datetime import datetime

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
    
    # grab PAST events affiliated with orgs that are affiliated with the user
    select_query = "SELECT E.event_id, E.title, O.org_name FROM events E, hosts H, affiliated_with A, organizations O WHERE E.event_id = H.event_id and H.org_id = A.org_id and H.org_id = O.org_id and A.user_id = '%s' and E.datetime_start <= now() order by E.datetime_start" % (user_id)
    cursor = g.conn.execute(text(select_query))
    past_events = []
    for result in cursor:
        past_events.append(result)
    # FUTURE events
    select_query = "SELECT E.event_id, E.title, O.org_name FROM events E, hosts H, affiliated_with A, organizations O WHERE E.event_id = H.event_id and H.org_id = A.org_id and H.org_id = O.org_id and A.user_id = '%s' and E.datetime_start > now() order by E.datetime_start" % (user_id)
    cursor = g.conn.execute(text(select_query))
    future_events = []
    for result in cursor:
        future_events.append(result)
    
    return render_template("hub.html", orgs = orgs, user_id = user_id, email = email, past_events = past_events, future_events = future_events)

# url routing for custom org page
@app.route('/org/<org_id>')
def org_profile(org_id):

    # grab org info from sql query
    select_query = "SELECT * FROM organizations WHERE org_id = '%s'" % (org_id)
    cursor = g.conn.execute(text(select_query))
    org = cursor.fetchone()

    # grab users affiliated with org from query
    select_query = "SELECT u.user_id, u.user_email, u.password  FROM organizations o JOIN affiliated_with aw ON aw.org_id = o.org_id JOIN users u on aw.user_id = u.user_id WHERE o.org_id = '%s'" % (org_id)
    cursor = g.conn.execute(text(select_query))
    print(select_query)
    users = []
    for result in cursor:
        users.append(result)
    print(result)	

    # grab PAST events affiliated with org
    select_query = "SELECT * FROM events E, hosts H WHERE E.event_id = H.event_id and H.org_id = '%s' and E.datetime_start <= now() ORDER BY E.datetime_start" % (org_id)
    cursor = g.conn.execute(text(select_query))
    past_events = []
    for result in cursor:
        past_events.append(result)
    
    # FUTURE events
    select_query = "SELECT * FROM events E, hosts H WHERE E.event_id = H.event_id and H.org_id = '%s' and E.datetime_start > now() ORDER BY E.datetime_start" % (org_id)
    cursor = g.conn.execute(text(select_query))
    future_events = []
    for result in cursor:
        future_events.append(result)

    return render_template("org_profile.html", org = org, users = users, past_events = past_events, future_events = future_events)

# url routing for custom events page
@app.route('/event/<event_id>')
def event_profile(event_id):

    # grab event info from sql query
    select_query = "SELECT * FROM events WHERE event_id = '%s'" % (event_id)
    cursor = g.conn.execute(text(select_query))
    print(select_query)
    events = []
    for result in cursor:
        events.append(result)
    print(events)

    # grab org_id of event host
    select_query = "SELECT * FROM organizations O JOIN hosts H ON O.org_id = H.org_id WHERE H.event_id = '%s'" % (event_id)
    cursor = g.conn.execute(text(select_query))
    print(select_query)
    orgs = []
    for result in cursor:
        orgs.append(result)

    # grab expenses info from sql query
    select_query = "SELECT * FROM expenses WHERE event_id = '%s'" % (event_id)
    cursor = g.conn.execute(text(select_query))
    print(select_query)
    expenses = []
    for result in cursor:
        expenses.append(result)
    print(expenses)
 
     # grab total expense from sql query
    select_query = "SELECT sum(cost) FROM expenses WHERE event_id = '%s'" % (event_id)
    cursor = g.conn.execute(text(select_query))
    total_expense = cursor.fetchone()[0]
    
    # grab affiliates info from sql query
    select_query = "SELECT * FROM affiliates WHERE event_id = '%s'" % (event_id)
    cursor = g.conn.execute(text(select_query))
    print(select_query)
    affiliates = []
    for result in cursor:
        affiliates.append(result)
        
    # grab financiers info from sql query
    select_query = "SELECT * FROM financiers WHERE event_id = '%s'" % (event_id)
    cursor = g.conn.execute(text(select_query))
    print(select_query)
    financiers = []
    for result in cursor:
        financiers.append(result)
        
    # get date
    now = datetime.now()
    
    return render_template("event_profile.html", events = events, orgs = orgs, expenses = expenses, total_expense = total_expense, affiliates = affiliates, financiers = financiers, now = now)


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
    ## * figure out how to condense this
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
  
      # query events
    select_query = "SELECT * FROM events"
    cursor = g.conn.execute(text(select_query))
    events = []
    for result in cursor:
        events.append(result)
  
      # query expenses
    select_query = "SELECT * FROM expenses"
    cursor = g.conn.execute(text(select_query))
    expenses = []
    for result in cursor:
        expenses.append(result)
  
    # query financiers
    select_query = "SELECT * FROM financiers"
    cursor = g.conn.execute(text(select_query))
    financiers = []
    for result in cursor:
        financiers.append(result)

    # query affiliates
    select_query = "SELECT * FROM affiliates"
    cursor = g.conn.execute(text(select_query))
    affiliates = []
    for result in cursor:
        affiliates.append(result)
  
    cursor.close()
    return render_template("admin.html", orgs = orgs, users = users, events=events,expenses=expenses, financiers=financiers, affiliates=affiliates)

# add org form
@app.route('/add_org', methods=["GET", "POST"])
def add_org():
    # accessing form inputs from user
    org_name = request.form.get("org_name")
    org_desc = "'%s'" % (request.form.get("org_desc")) if request.form.get("org_desc") != "" else "NULL"
    org_email = "'%s'" % (request.form.get("org_email")) if request.form.get("org_email") != "" else "NULL"
    marketing_email = "'%s'" % (request.form.get("marketing_email")) if request.form.get("marketing_email") != "" else "NULL"
    comms_email = "'%s'" % (request.form.get("comms_email")) if request.form.get("comms_email") != "" else "NULL"
    finance_email = "'%s'" % (request.form.get("finance_email")) if request.form.get("finance_email") != "" else "NULL"
    advisor_email = request.form.get("advisor_email")

    # new org_id is highest org_id + 1
    select_query = "SELECT max(org_id) FROM organizations"
    cursor = g.conn.execute(text(select_query))
    org_id = str(int(cursor.fetchone()[0]) + 1).zfill(4) # fill with leading 0's [0001, 0002]

    # query to add org to organizations table
    select_query = "INSERT INTO organizations (org_id, org_name, org_description, org_email, marketing_email, comms_email, finance_email, advisor_email) VALUES ('%s', '%s', %s, %s, %s, %s, %s, '%s')" % (org_id, org_name, org_desc, org_email, marketing_email, comms_email, finance_email, advisor_email)
    print(select_query)
    g.conn.execute(text(select_query))
    g.conn.commit()

    # query to add affiliated_with linking logged in user w/ org
    select_query = "INSERT INTO affiliated_with (user_id, org_id) VALUES ('%s', '%s')" % (user_id, org_id)
    print(select_query)
    g.conn.execute(text(select_query))
    g.conn.commit()

    return redirect('/hub')

@app.route('/org/<org_id>', methods=["GET", "POST"])
def add_event(org_id):
    title = request.form.get("title")
    description = "'%s'" % (request.form.get("description")) if request.form.get("description") != "" else "NULL"
    location = "'%s'" % (request.form.get("location")) if request.form.get("location") != "" else "NULL"
    datetime_start = "'%s'" % (request.form.get("datetime_start")) if request.form.get("datetime_start") != "" else "NULL"
    datetime_end = "'%s'" % (request.form.get("datetime_end")) if request.form.get("datetime_end") != "" else "NULL"
    budget = "%s" % (request.form.get("budget")) if request.form.get("budget") != "" else "NULL"
    liason_name = "'%s'" % (request.form.get("liason_name")) if request.form.get("liason_name") != "" else "NULL"
    liason_email = "'%s'" % (request.form.get("liason_email")) if request.form.get("liason_email") != "" else "NULL"
    approved = "'%s'" % (request.form.get("approved")) if request.form.get("approved") != "" else "NULL"

    # new event_id is highest event_id + 1
    select_query = "SELECT max(event_id) FROM events"
    cursor = g.conn.execute(text(select_query))
    event_id = str(int(cursor.fetchone()[0]) + 1).zfill(5) # fill with leading 0's [0001, 0002]

    # query to add event to events tableç
    select_query = "INSERT INTO events (event_id, title, approved, liason_name, liason_email, description, location, datetime_start, datetime_end, budget) VALUES ('%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s)" % (event_id, title, approved, liason_name, liason_email, description, location, datetime_start, datetime_end, budget)
    print(select_query)
    g.conn.execute(text(select_query))
    g.conn.commit()

    # query to add (event,org) pair to hosts table
    select_query = "INSERT INTO hosts (org_id, event_id) VALUES ('%s', '%s')" % (org_id, event_id)
    g.conn.execute(text(select_query))
    g.conn.commit()

    return redirect(("/org/%s") % (org_id))


@app.route('/<event_id>/update_event', methods=["GET", "POST"])
def update_event(event_id):
    title = request.form.get("title")
    description = "'%s'" % (request.form.get("description")) if request.form.get("description") != "" else "NULL"
    location = "'%s'" % (request.form.get("location")) if request.form.get("location") != "" else "NULL"
    datetime_start = "'%s'" % (request.form.get("datetime_start")) if request.form.get("datetime_start") != "" else "NULL"
    datetime_end = "'%s'" % (request.form.get("datetime_end")) if request.form.get("datetime_end") != "" else "NULL"
    budget = "%s" % (request.form.get("budget")) if request.form.get("budget") != "" else "NULL"
    liason_name = "'%s'" % (request.form.get("liason_name")) if request.form.get("liason_name") != "" else "NULL"
    liason_email = "'%s'" % (request.form.get("liason_email")) if request.form.get("liason_email") != "" else "NULL"
    approved = "'%s'" % (request.form.get("approved")) if request.form.get("approved") != "" else "NULL"

    # query to update event in events table
    select_query = "UPDATE events SET title = '%s', approved = '%s', liason_name = '%s', liason_email = '%s', description = '%s', location = '%s', datetime_start = '%s', datetime_end = '%s', budget = '%s' WHERE event_id = '%s'" % (title, approved, liason_name, liason_email, description, location, datetime_start, datetime_end, budget, event_id)
    print(select_query)
    g.conn.execute(text(select_query))
    g.conn.commit()

    return redirect("/event/%s" % (event_id))


## ** Figure how to link this to the event_id of the event it's affiliated with !!!
# add expenses form
@app.route('/<event_id>/add_expense', methods=["GET", "POST"])
def add_expense(event_id):
    #event_id = request.script_root[1:] # grab event_id from url
    # accessing form inputs from user
    item_name = request.form.get("item_name")
    cost = request.form.get("cost")

    # new expense_id is highest expense_id + 1
    select_query = "SELECT max(item_id) FROM expenses"
    cursor = g.conn.execute(text(select_query))
    item_id = str(int(cursor.fetchone()[0]) + 1).zfill(5) # fill with leading 0's [0001, 0002]

    # query to add org to expenses table
    select_query = "INSERT INTO expenses (item_id, event_id, item_name, cost) VALUES ('%s', '%s', %s, %s)" % (item_id, event_id, item_name, cost)
    print(select_query)
    g.conn.execute(text(select_query))
    g.conn.commit()

    return redirect("/event/%s" % (event_id))

## ** Figure how to link this to the event_id of the event it's affiliated with !!!
# update expenses form
@app.route('/<event_id>/update_expense', methods=["GET", "POST"])
def update_expense(event_id):
    #event_id = request.script_root[1:] # grab event_id from url
    item_id = request.form.get("item_id")

    if request.form.get("delete_request") != None: # delete box is checked
        # query to remove expense from expenses table
        select_query = "DELETE from expenses WHERE item_id = '%s' and event_id = '%s'" % (item_id, event_id)
        print(select_query)
        g.conn.execute(text(select_query))
        g.conn.commit()
        
    else: 
        # accessing form inputs from user
        item_name = request.form.get("item_name")
        cost = request.form.get("cost")

        # query to add expense to expenses table
        select_query = "UPDATE expenses SET item_name = '%s', cost = '%s' WHERE item_id = '%s' and event_id = '%s'" % (item_name, cost, item_id, event_id)
        print(select_query)
        g.conn.execute(text(select_query))
        g.conn.commit()

    return redirect("/event/%s" % (event_id))


@app.route('/<event_id>/add_financier', methods=["GET", "POST"])
def add_financier(event_id):
    financier_email = request.form.get("financier_email")
    company = request.form.get("company")
    amount_sponsored = request.form.get("amount_sponsored")

    # generate fin_id
    select_query = "SELECT max(fin_id) FROM financiers"
    cursor = g.conn.execute(text(select_query))
    fin_id = str(int(cursor.fetchone()[0]) + 1).zfill(4) # fill with leading 0's [0001, 0002]

    # add financier to financier table
    select_query = "INSERT INTO financiers (fin_id, event_id, financier_email, company, amount_sponsored) VALUES ('%s', '%s', '%s', '%s', '%s')" % (fin_id, event_id, financier_email, company, amount_sponsored)
    print(select_query)
    g.conn.execute(text(select_query))
    g.conn.commit()

    return redirect("/event/%s" % (event_id))


@app.route('/<event_id>/update_financier', methods=["GET", "POST"])
def update_financier(event_id):
    fin_id = request.form.get("fin_id")

    # delete financier
    if request.form.get("delete_request_f") != None:
        select_query = "DELETE from financiers WHERE fin_id = '%s' and event_id = '%s'" % (fin_id, event_id)
        print(select_query)
        g.conn.execute(text(select_query))
        g.conn.commit()
    else:
        financier_email = request.form.get("financier_email")
        company = request.form.get("company")
        amount_sponsored = request.form.get("amount_sponsored")
        select_query = "UPDATE financiers SET financier_email = '%s', company = '%s', amount_sponsored = '%s' WHERE fin_id = '%s' and event_id = '%s'" % (financier_email, company, amount_sponsored, fin_id, event_id)
        print(select_query)
        g.conn.execute(text(select_query))
        g.conn.commit()

    return redirect("/event/%s" % (event_id))


@app.route('/<event_id>/add_affiliate', methods=["GET", "POST"])
def add_affiliate(event_id):
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    position = request.form.get("position")
    status = request.form.get("status")

    # generate aff_id
    select_query = "SELECT max(aff_id) FROM affiliates"
    cursor = g.conn.execute(text(select_query))
    aff_id = str(int(cursor.fetchone()[0]) + 1).zfill(5) # fill with leading 0's [0001, 0002]

    # add affiliate to affiliates table
    select_query = "INSERT INTO affiliates (aff_id, event_id, name, email, phone, position, status) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (aff_id, event_id, name, email, phone, position, status)
    print(select_query)
    g.conn.execute(text(select_query))
    g.conn.commit()

    return redirect("/event/%s" % (event_id))


@app.route('/<event_id>/update_affiliate', methods=["GET", "POST"])
def update_affiliate(event_id):
    aff_id = request.form.get("aff_id")

    # delete affiliate
    if request.form.get("delete_request_a") != None:
        select_query = "DELETE from affiliates WHERE aff_id = '%s' and event_id = '%s'" % (aff_id, event_id)
        print(select_query)
        g.conn.execute(text(select_query))
        g.conn.commit()
    else:
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        position = request.form.get("position")
        status = request.form.get("status")
        select_query = "UPDATE affiliates SET name = '%s', email = '%s', phone = '%s', position = '%s', status = '%s' WHERE aff_id = '%s' and event_id = '%s'" % (name, email, phone, position, status, aff_id, event_id)
        print(select_query)
        g.conn.execute(text(select_query))
        g.conn.commit()

    return redirect("/event/%s" % (event_id))


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
