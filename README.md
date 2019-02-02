# Udacity: Unit 4 Project: Catalog

This app is a catalog for a sports store.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

#### Prerequisites to run the application

* Install Flask with `pip install Flask`.
* Install SQLAlchemy with `pip install SQLAlchemy`.
* Install oauth2client with `pip install oauth2client`.
* Install apiclient with `pip install apiclient`.

#### Installing the files

* Copy the project files including the `application.py` file into the vagrant folder that is accessible in your virtual machine.

## Running the application

#### Setting up the server
* Go to the location of your vagrant virtual machine.
* Start up your virtual machine with `vagrant up`.
* Log into your virtual machine with `vagrant ssh`.
* Navigate into the catalog folder within the vagrant folder and start the server with `python application.py`.

### Using the appliction
* In your browser of choice go to [http://localhost:8000](http://localhost:8000)

##### Navigating the application
* Using the navbar
	* The store name also doubles as link to return home.
	* on the right side of the navbar is a place to sign in/ sign out with a Google account
* The homepage displays all of the departments from the store database.
	* If the user is logged in they can add, edit, or delete departments
* If a department name is clicked, it will display all of the items for that department from the store database.
	* If the user is logged in they can add, edit, or delete the items in the department
* If an item name is clicked, it will display all of the information for that item from the store database.
	* If the user is logged in they can add, edit, or delete the item