# Imports for flask
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from flask import session as login_session
# Imports for database calls
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker, joinedload
from database_setup import Base, Department, DepartmentItem, User
# Import for user login
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
# Other imports for various functions
import random
import string
import httplib2
import json
import requests

from apiclient import discovery
from oauth2client import client

# Setup for functionality with flask
application = Flask(__name__)


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)


# Code to log in user to app through Google
@application.route('/gconnect', methods=['POST'])
def gconnect():
    CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'.format(access_token))
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['provider'] = 'google'
    login_session['gplus_id'] = gplus_id
    if data['name']:
        login_session['username'] = data['name']
    if data['picture']:
        login_session['picture'] = data['picture']
    if data['email']:
        login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as {}".format(login_session['username']))
    print "done!"
    return output

def createUser(login_session):
    session = DBSession()
    newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

def getUserID(email):
    try:
        session = DBSession()
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

def getUserInfo(user_id):
    session = DBSession()
    user = session.query(User).filter_by(id = user_id).one()
    return user

def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is {}'.format(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("You have been logged out")
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# Creates anti-forgery state token and directs user to login page
@application.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', path='login', STATE=state)

# Route used to log user out
@application.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        return redirect(url_for('showDepartments'))
    else:
        flash('You were not logged in to begin with!')
        return redirect(url_for('showDepartments'))

#  [-------- Department Pages --------]
# Show all departments
@application.route('/departments')
@application.route('/')
def showDepartments():
    session = DBSession()
    departments = session.query(Department).order_by(asc(Department.name)).all()
    if 'username' not in login_session:
        return render_template('departments.html', departments=departments)
    else:
        return render_template('departmentsUser.html', departments=departments)

# Create New Department
@application.route('/departments/create', methods=['GET','POST'])
def createDepartment():
    session = DBSession()

    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        newDepartment = Department(name=request.form['name'], user_id = login_session['user_id'])
        session.add(newDepartment)
        flash('{} Successfully Created'.format(newDepartment.name))
        session.commit()
        return redirect(url_for('showDepartments'))
    else:
        return render_template('createDepartment.html', path='Create Department')

# Edit Department
@application.route('/departments/<int:department_id>/edit', methods=['GET','POST'])
def editDepartment(department_id):
    session = DBSession()

    if 'username' not in login_session:
        return redirect('/login')
    
    editDepartment = session.query(Department).filter_by(id=department_id).one()
    if request.method == 'POST':
        
        if request.form['name']:
            editDepartment.name = request.form['name']
        session.add(editDepartment)
        flash('{} Successfully Updated'.format(editDepartment.name))
        session.commit()
        return redirect(url_for('showDepartments'))
    else:
        return render_template('editDepartment.html', path='Edit {}'.format(editDepartment.name), department=editDepartment)

# Delete Department
@application.route('/departments/<int:department_id>/delete/', methods=['GET', 'POST'])
def deleteDepartment(department_id):
    session = DBSession()

    if 'username' not in login_session:
        return redirect('/login')

    departmentToDelete = session.query(Department).filter_by(id=department_id).one()
    if request.method == 'POST':
        session.delete(departmentToDelete)
        flash('{} Successfully Deleted'.format(departmentToDelete.name))
        session.commit()
        return redirect(url_for('showDepartments'))
    else:
        return render_template('deleteDepartment.html', path='Delete {}'.format(departmentToDelete.name), department=departmentToDelete)

@application.route('/departments/JSON')
def departmentsJSON():
    session = DBSession()
    merchandise = session.query(Department).options(joinedload(Department.items)).all()
    return jsonify(dict(Department=[dict(m.serializable, Items=[i.serializable for i in m.items]) for m in merchandise]))
    return jsonify(items=[i.serialize for i in merchandise])

#  [-------- Item Pages --------]
# Show Items From A Certain Department
@application.route('/departments/<int:department_id>')
def showDepartmentItems(department_id):
    session = DBSession()
    departments = session.query(Department).order_by(asc(Department.name)).all()
    department = session.query(Department).filter_by(id=department_id).one()
    departmentItems = session.query(DepartmentItem).filter_by(department_id=department_id).all()
    if 'username' not in login_session:
        return render_template('departmentItems.html', path='{} Items'.format(department.name), departments=departments, departmentItems=departmentItems, department=department)
    else:
        return render_template('departmentItemsUser.html', path='{} Items'.format(department.name), departments=departments, departmentItems=departmentItems, department=department)

# Create New Item
@application.route('/departments/<int:department_id>/create', methods=['GET','POST'])
def createDepartmentItem(department_id):
    session = DBSession()

    if 'username' not in login_session:
        return redirect('/login')

    department = session.query(Department).filter_by(id=department_id).one()
    if request.method == 'POST':
        newItem = DepartmentItem(name=request.form['name'], department=department,  description=request.form['description'], price=request.form['price'], user_id = login_session['user_id'])
        session.add(newItem)
        flash('{} Successfully Created'.format(newItem.name))
        session.commit()
        return redirect(url_for('showDepartmentItems', department_id=department_id))
    else:
        return render_template('createDepartmentItem.html', path='Create New Item for {}'.format(department.name), department=department)

# Edit Item
@application.route('/departments/<int:department_id>/<int:item_id>/edit', methods=['GET','POST'])
def editDepartmentItem(department_id, item_id):
    session = DBSession()

    if 'username' not in login_session:
        return redirect('/login')
    
    department = session.query(Department).filter_by(id=department_id).one()
    editDepartmentItem = session.query(DepartmentItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        
        if request.form['name']:
            editDepartmentItem.name = request.form['name']
        if request.form['description']:
            editDepartmentItem.description = request.form['description']
        if request.form['price']:
            editDepartmentItem.price = request.form['price']
        session.add(editDepartmentItem)
        flash('{} Successfully Updated'.format(editDepartmentItem.name))
        session.commit()
        return redirect(url_for('showDepartmentItems', department_id=department.id))
    else:
        return render_template('editDepartmentItem.html', path='Edit {}'.format(editDepartmentItem.name), department=department, item=editDepartmentItem)

# Delete Item
@application.route('/departments/<int:department_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteDepartmentItem(department_id, item_id):
    session = DBSession()

    if 'username' not in login_session:
        return redirect('/login')

    department = session.query(Department).filter_by(id=department_id).one()
    itemToDelete = session.query(DepartmentItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        flash('{} Successfully Deleted'.format(itemToDelete.name))
        session.commit()
        return redirect(url_for('showDepartmentItems', department_id=department.id))
    else:
        return render_template('deleteDepartmentItem.html', path='Delete {}'.format(itemToDelete.name), department=department, item=itemToDelete)

@application.route('/departments/<int:department_id>/<int:item_id>/description')
def showItemDescription(department_id, item_id):
    session = DBSession()

    departments = session.query(Department).order_by(asc(Department.name)).all()
    department = session.query(Department).filter_by(id=department_id).one()
    item = session.query(DepartmentItem).filter_by(id=item_id).one()
    return render_template('itemDescription.html', path='{}'.format(item.name), departments=departments, department=department, item=item)


if __name__ == '__main__':
    application.secret_key = 'super_secret_key'
    application.debug = True
    application.run()
