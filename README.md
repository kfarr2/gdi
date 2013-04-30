# Install
## Environment

To build `python-ldap` with pip on centos, you need the `openldap24-libs-devel` package.

    yum install openldap24-libs-devel

And when you install python-ldap with pip, you need to set these envars:
    
    export CPATH=/usr/include/openldap24
    export LIBRARY_PATH=/usr/lib/openldap24/

Create a virtual environment, and install the required packages in it:

    virtualenv-2.6 --no-site-packages .env
    source .env/bin/activate
    pip install -r requirements.txt

## Settings

Create a settings file from the template, and fill in the blanks:

    cp mentoring/demo_settings.py mentoring/local_settings.py
    vim mentoring/local_settings.py

## Database

Clone the database from mysql.rc.pdx.edu:

    mysqldump -u USERNAME -p -h mysql.rc.pdx.edu gdi > sql.sql
    echo "CREATE DATABASE gdi;" | mysql -u root
    mysql -u root gdi < sql.sql

# Run

To run the app use Django's built in web server: 

    ./manage runserver 10.0.0.10 8000

replace 10.0.0.10 with your VM's IP


