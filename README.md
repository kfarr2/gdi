# Django Quickstart
This is a Django project template that lets you get started on a Django project right away.

Setup some environment variables so you can just copy and paste the rest of the commands:

    DOMAIN="helloworld.com"
    PROJECT_NAME="helloworld"

Create a directory for your django project and start a virtual environment:

    adduser $DOMAIN
    cd $(getent passwd $DOMAIN | cut -d: -f6) # this just gets the user's homedir, and cds to it
    virtualenv-2.6 --no-site-packages .env
    source .env/bin/activate
    pip install django

Start a new Django project using this git repo as a template:

    django-admin.py startproject --extension=py,conf --template=https://github.com/mdj2/django/archive/master.zip $PROJECT_NAME .

Install the neccessary packages, and make manage.py executable

    pip install -r requirements.txt
    chmod +x manage.py

Update the settings in `$PROJECT_NAME`/local_settings.py. Make sure you create the database it tries to connect to.

    vim $PROJECT_NAME/local_settings.py

And run (assuming 10.0.0.10 is your VM's IP address):

    ./manage.py runserver 10.0.0.10:8000

Point your browser to 10.0.0.10:8000

Write over this file with a README specific to your project. Init a repo:

    echo "# This is my project" > README.md
    git init
    git add .
    git commit -m "Initial commit"

# Getting Started with Django (from scratch)

## Environment
Create a directory for your entire web project. On my own dev VM, I like to create a new user for the project, and use the homedir as the project dir:

    adduser helloworld.com
    cd ~helloworld.com
    # get rid of all the dotfile garbage with this:
    # rm -rf .*

Python is usually installed on the OS, and probably has a bunch of third party packages already installed. Generally, it's a good idea to _not_ rely on any packages installed by the OS. Your app should be self contained; only the Python packages that you need should be available. Fortunately, a program called virtualenv makes it easy to setup isolated Python environments for every app you build. In your project directory, create a new virtual environment:

    cd ~helloworld.com
    virtualenv-2.6 --no-site-packages .env

If you `echo $PATH`, you'll notice that your virtual environment is nowhere to be found. To start using the virtual environment, you need to `source` it:

    source .env/bin/activate

Now if you `echo $PATH`, you'll see entries for various directories in .env. If you ever need to reset your `$PATH` back to normal, just type `deactivate`.

## Install Packages
Assuming your virtual environment is in your `$PATH`, you can start installing packages now for your Django project. Typically, you need Django (surprise, surprise), and some kind of database library like mysql-python, or psycopg2. Packages can easily be installed with pip:

    pip install django
    pip install mysql-python

Always make sure you keep an up-to-date list of packages that your app requires. This is easy to do with pip. Whenever you install a new package with pip, just run (from your project's root directory):

    pip freeze > requirements.txt

Now when someone comes along and wants to deploy your awesome Django app, they can just run:

    pip install -r requirements.txt

to install all the required packages.

## Creating a Django Project
Django comes with a program called django-admin.py that performs various functions. One of them helps you create an initial project. In our home project directory, start a new django project:

    django-admin.py startproject helloworld .

I usually name my projects after the website's domain name (minus the tld).

This will create a new directory called `helloworld` in the current working directory. `helloworld` will have some files in it like:

    __init__.py  settings.py  urls.py  wsgi.py

It also creates a file called manage.py in the current working directory. manage.py is essentially the same thing as django-admin.py, except it knows about the project specific settings (i.e. the helloworld/settings.py file).

### Configuration
Cd into your Django project directory `cd ~helloworld.com/helloworld` and start making changes to the settings.
#### settings.py
As of this writing, Django's default settings.py file leaves much to be desired. So we have to make a lot of changes. Open settings.py up in favorite text editor...

Insert these lines at the very top of the file:

    import os
    PROJECT_DIR = os.path.dirname(__file__)
    HOME_DIR = os.path.normpath(os.path.join(PROJECT_DIR, '../'))

This allows you to point to various parts of your project without hard coding the path anywhere in your Django project. It makes your project more portable.

Change your timezone to UTC:

    TIME_ZONE = 'UTC'

Use your fancy HOME_DIR variable to tell Django where to find static files (like CSS, JS and images). Note, we haven't actually created this directory yet (we will, don't worry):

    STATICFILES_DIRS = (
        os.path.join(HOME_DIR, "htdocs", "static"),
    )

Again, use your fancy PROJECT_DIR variable to specify where Django should search for template files:

    TEMPLATE_DIRS = (
        os.path.join(PROJECT_DIR, 'templates'),
    )

At the _very_ bottom of settings.py add:

    from local_settings import *

This tells Django to look for a file called local_settings.py and import whatever settings are in there.

#### demo_settings.py
Create a new file called demo_settings.py. _Move_ (cut and paste) the following settings from settings.py into demo_settings.py:

    DEBUG
    TEMPLATE_DEBUG
    ADMINS
    MANAGERS
    DATABASES
    SECRET_KEY

demo_settings.py serves as a template for your deployment specific settings (like the database connection parameters, and debug settings).

#### local_settings.py
This is where your actual settings for the project go. We use demo_settings.py as a template for this file:
Copy demo_settings.py to local_settings.py

    cp demo_settings.py local_settings.py

Modify the database connections parameters, and other settings as you see fit.

Go back into demo_settings.py and set the secret key to the empty string (we don't want a real secret key hanging out in our template).

## Directory Structure
Remember in the settings.py we pointed at some directories like htdocs/static and templates? We still need to create those:

    cd ~helloworld.com
    mkdir -p htdocs/static/css
    mkdir -p htdocs/static/js
    mkdir -p htdocs/static/img
    mkdir -p helloworld/templates

Let's create some dummy files while we're at it:

    echo "body { background-color:#efefef; }" > htdocs/static/css/main.css
    echo "console.log('hello')" > htdocs/static/js/main.js
    > htdocs/static/img/blank.png
    > htdocs/static/favicon.ico
    > htdocs/static/robots.txt

## Git
In your project root directory `cd ~helloworld.com`:

    git init
    echo ".env" >> .gitignore
    echo "*.pyc" >> .gitignore
    echo "local_settings.py" >> .gitignore

We ignore the .env directory because it can't be rebuilt with `pip install -r requirements.txt`. local_settings.py is ignored because it contains sensitive settings that should not _ever_ be in version control. Make your commit:

    git add .
    git commit -m "Initial commit"
    
Now try to run your Django project with the built in server:

    python manage.py runserver <YOUR IP ADDRESS>:8000
  
Point a browser to `<YOUR IP ADDRESS>:8000` and be amazed.


