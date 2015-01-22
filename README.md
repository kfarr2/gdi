# Install
## Environment

To build `python-ldap` with pip on centos, you need the `openldap24-libs-devel` package.

    yum install openldap24-libs-devel

Then just

    make install
    source .env/bin/activate

## Database

Clone the database from mysql.rc.pdx.edu:

    mysqldump -u USERNAME -p -h mysql.rc.pdx.edu gdi > sql.sql
    echo "CREATE DATABASE gdi;" | mysql -u root
    mysql -u root gdi < sql.sql

# Run

To run the app use Django's built in web server: 

    make

# Testing

To run tests normally:

    make test

To run tests with coverage:

    make cover

and visit 0.0.0.0:8000/htmlcov/index.html

