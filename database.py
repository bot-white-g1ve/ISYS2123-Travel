#!/usr/bin/env python3
# Imports
from modules import pg8000
import configparser
import sys
from hashlib import blake2b
from hmac import compare_digest
import os
import routes

#  Common Functions
##     database_connect()
##     dictfetchall(cursor,sqltext,params)
##     dictfetchone(cursor,sqltext,params)
##     print_sql_string(inputstring, params)


################################################################################
# Connect to the database
#   - This function reads the config file and tries to connect
#   - This is the main "connection" function used to set up our connection
################################################################################

def database_connect():
    # Read the config file
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Create a connection to the database
    connection = None

    # choose a connection target, you can use the default or
    # use a different set of credentials that are setup for localhost or winhost
    connectiontarget = 'DATABASE'
    # connectiontarget = 'DATABASELOCAL'
    try:
        '''
        This is doing a couple of things in the back
        what it is doing is:

        connect(database='y2?i2120_unikey',
            host='soit-db-pro-2.ucc.usyd.edu.au,
            password='password_from_config',
            user='y2?i2120_unikey')
        '''
        targetdb = ""
        if ('database' in config[connectiontarget]):
            targetdb = config[connectiontarget]['database']
        else:
            targetdb = config[connectiontarget]['user']

        connection = pg8000.connect(database=targetdb,
                                    user=config[connectiontarget]['user'],
                                    password=config[connectiontarget]['password'],
                                    host=config[connectiontarget]['host'],
                                    port=int(config[connectiontarget]['port']))
    except pg8000.OperationalError as e:
        print("""Error, you haven't updated your config.ini or you have a bad
        connection, please try again. (Update your files first, then check
        internet connection)
        """)
        print(e)
    except pg8000.ProgrammingError as e:
        print("""Error, config file incorrect: check your password and username""")
        print(e)
    except Exception as e:
        print(e)

    # Return the connection to use
    return connection

######################################
# Database Helper Functions
######################################
def dictfetchall(cursor,sqltext,params=None):
    """ Returns query results as list of dictionaries."""
    """ Useful for read queries that return 1 or more rows"""

    result = []
    
    cursor.execute(sqltext,params)
    if cursor.description is not None:
        cols = [a[0].decode("utf-8") for a in cursor.description]
        
        returnres = cursor.fetchall()
        if returnres is not None or len(returnres > 0):
            for row in returnres:
                result.append({a:b for a,b in zip(cols, row)})

        # cursor.close()
    print("returning result: ",result)
    return result

def dictfetchone(cursor,sqltext,params=None):
    """ Returns query results as list of dictionaries."""
    """ Useful for create, update and delete queries that only need to return one row"""

    # cursor = conn.cursor()
    result = []
    cursor.execute(sqltext,params)
    if (cursor.description is not None):
        print("cursor description", cursor.description)
        cols = [a[0].decode("utf-8") for a in cursor.description]
        returnres = cursor.fetchone()
        print("returnres: ", returnres)
        if (returnres is not None):
            result.append({a:b for a,b in zip(cols, returnres)})
    return result

##################################################
# Print a SQL string to see how it would insert  #
##################################################

def print_sql_string(inputstring, params=None):
    """
    Prints out a string as a SQL string parameterized assuming all strings
    """
    if params is not None:
        if params != []:
           inputstring = inputstring.replace("%s","'%s'")
    
    print(inputstring % params)

###############
# Login       #
###############

def check_login(username, password):
    '''
    Check Login given a username and password
    '''
    # Ask for the database connection, and get the cursor set up
    conn = database_connect()
    print("checking login")
    if(conn is None):
        return None
    cur = conn.cursor()
    try:
        # Try executing the SQL and get from the database
        
        sql = """SELECT *
                FROM opaltravel.Users
                    JOIN opaltravel.UserRoles ON
                        (opaltravel.Users.userroleid = opaltravel.UserRoles.userroleid)
                WHERE userid=%s"""
        print_sql_string(sql, (username,))
        r = dictfetchone(cur, sql, (username,)) # Fetch the first row
        cur.close()                     # Close the cursor
        conn.close()                    # Close the connection to the db
        if r is not None:
            if check_password(password, r[0]['password']):
                return r
            else:
                #print(str(r[0]['password']))
                #print(check_password(password, r[0]['password']))
                print("Wrong password")
                return None
    except Exception as e:
        # If there were any errors, return a NULL row printing an error to the debug
        print("Error Invalid Login:", str(e))
    cur.close()                     # Close the cursor
    conn.close()                    # Close the connection to the db
    return None
    
########################
#List All Items#
########################

# Get all the rows of users and return them as a dict
def list_users():
    # Get the database connection and set up the cursor
    conn = database_connect()
    if(conn is None):
        # If a connection cannot be established, send an Null object
        return None
    # Set up the rows as a dictionary
    cur = conn.cursor()
    returndict = None

    try:
        # Set-up our SQL query
        sql = """SELECT *
                    FROM opaltravel.users """
        
        # Retrieve all the information we need from the query
        returndict = dictfetchall(cur,sql)

        # report to the console what we recieved
        print(returndict)
    except:
        # If there are any errors, we print something nice and return a null value
        print("Error Fetching from Database", sys.exc_info()[0])

    # Close our connections to prevent saturation
    cur.close()
    conn.close()

    # return our struct
    return returndict
    

def list_userroles():
    # Get the database connection and set up the cursor
    conn = database_connect()
    if(conn is None):
        # If a connection cannot be established, send an Null object
        return None
    # Set up the rows as a dictionary
    cur = conn.cursor()
    returndict = None

    try:
        # Set-up our SQL query
        sql = """SELECT *
                    FROM opaltravel.userroles """
        
        # Retrieve all the information we need from the query
        returndict = dictfetchall(cur,sql)

        # report to the console what we recieved
        print(returndict)
    except:
        # If there are any errors, we print something nice and return a null value
        print("Error Fetching from Database", sys.exc_info()[0])

    # Close our connections to prevent saturation
    cur.close()
    conn.close()

    # return our struct
    return returndict
    

########################
#List Single Items#
########################

# Get all rows in users where a particular attribute matches a value
def list_users_equifilter(attributename, filterval):
    # Get the database connection and set up the cursor
    conn = database_connect()
    if(conn is None):
        # If a connection cannot be established, send an Null object
        return None
    # Set up the rows as a dictionary
    cur = conn.cursor()
    val = None

    try:
        # Retrieve all the information we need from the query
        sql = f"""SELECT *
                    FROM opaltravel.users
                    WHERE {attributename} = %s """
        val = dictfetchall(cur,sql,(filterval,))
    except:
        # If there are any errors, we print something nice and return a null value
        print("Error Fetching from Database: ", sys.exc_info()[0])

    # Close our connections to prevent saturation
    cur.close()
    conn.close()

    # return our struct
    return val
    


########################### 
#List Report Items #
###########################
    
# # A report with the details of Users, Userroles
def list_consolidated_users():
    # Get the database connection and set up the cursor
    conn = database_connect()
    if(conn is None):
        # If a connection cannot be established, send an Null object
        return None
    # Set up the rows as a dictionary
    cur = conn.cursor()
    returndict = None

    try:
        # Set-up our SQL query
        sql = """SELECT *
                FROM opaltravel.users 
                    JOIN opaltravel.userroles 
                    ON (opaltravel.users.userroleid = opaltravel.userroles.userroleid) ;"""
        
        # Retrieve all the information we need from the query
        returndict = dictfetchall(cur,sql)

        # report to the console what we recieved
        print(returndict)
    except:
        # If there are any errors, we print something nice and return a null value
        print("Error Fetching from Database", sys.exc_info()[0])

    # Close our connections to prevent saturation
    cur.close()
    conn.close()

    # return our struct
    return returndict

def list_user_stats():
    # Get the database connection and set up the cursor
    conn = database_connect()
    if(conn is None):
        # If a connection cannot be established, send an Null object
        return None
    # Set up the rows as a dictionary
    cur = conn.cursor()
    returndict = None

    try:
        # Set-up our SQL query
        sql = """SELECT userroleid, COUNT(*) as count
                FROM opaltravel.users 
                    GROUP BY userroleid
                    ORDER BY userroleid ASC ;"""
        
        # Retrieve all the information we need from the query
        returndict = dictfetchall(cur,sql)

        # report to the console what we recieved
        print(returndict)
    except:
        # If there are any errors, we print something nice and return a null value
        print("Error Fetching from Database", sys.exc_info()[0])

    # Close our connections to prevent saturation
    cur.close()
    conn.close()

    # return our struct
    return returndict
    

####################################
##  Search Items - inexact matches #
####################################

# Search for users with a custom filter
# filtertype can be: '=', '<', '>', '<>', '~', 'LIKE'
def search_users_customfilter(attributename, filtertype, filterval):
    # Get the database connection and set up the cursor
    conn = database_connect()
    if(conn is None):
        # If a connection cannot be established, send an Null object
        return None
    # Set up the rows as a dictionary
    cur = conn.cursor()
    val = None

    # arrange like filter
    filtervalprefix = ""
    filtervalsuffix = ""
    if str.lower(filtertype) == "like":
        filtervalprefix = "'%"
        filtervalsuffix = "%'"
        
    try:
        # Retrieve all the information we need from the query
        sql = f"""SELECT *
                    FROM opaltravel.users
                    WHERE lower({attributename}) {filtertype} {filtervalprefix}lower(%s){filtervalsuffix} """
        print_sql_string(sql, (filterval,))
        val = dictfetchall(cur,sql,(filterval,))
    except:
        # If there are any errors, we print something nice and return a null value
        print("Error Fetching from Database: ", sys.exc_info()[0])

    # Close our connections to prevent saturation
    cur.close()
    conn.close()

    # return our struct
    return val


#####################################
##  Update Single Items by PK       #
#####################################


# Update a single user
def update_single_user(userid, firstname, lastname,userroleid,password):
    # Get the database connection and set up the cursor
    conn = database_connect()
    if(conn is None):
        # If a connection cannot be established, send an Null object
        return None
    # Set up the rows as a dictionary
    cur = conn.cursor()
    val = None

    # Data validation checks are assumed to have been done in route processing

    try:
        setitems = ""
        attcounter = 0
        if firstname is not None:
            setitems += "firstname = %s\n"
            attcounter += 1
        if lastname is not None:
            if attcounter != 0:
                setitems += ","
            setitems += "lastname = %s\n"
            attcounter += 1
        if userroleid is not None:
            if attcounter != 0:
                setitems += ","
            setitems += "userroleid = %s::bigint\n"
            attcounter += 1
        if password is not None:
            if attcounter != 0:
                setitems += ","
            setitems += "password = %s\n"
            attcounter += 1
        # Retrieve all the information we need from the query
        sql = f"""UPDATE opaltravel.users
                    SET {setitems}
                    WHERE userid = {userid};"""
        hashed_password = sign_password(password)
        print_sql_string(sql,(firstname, lastname,userroleid,hashed_password))
        val = dictfetchone(cur,sql,(firstname, lastname,userroleid,hashed_password))
        conn.commit()
        
    except:
        # If there are any errors, we print something nice and return a null value
        print("Error Fetching from Database: ", sys.exc_info()[0])
        print(sys.exc_info())

    # Close our connections to prevent saturation
    cur.close()
    conn.close()

    # return our struct
    return val


##  Insert / Add

def add_user_insert(firstname, lastname,userroleid,password):
    """
    Add a new User to the system
    """
    # Data validation checks are assumed to have been done in route processing

    conn = database_connect()
    if(conn is None):
        return None
    cur = conn.cursor()
    sql = """
        INSERT into opaltravel.Users(firstname, lastname, userroleid, password)
        VALUES (%s,%s,%s,%s);
        """
    hashed_password = sign_password(password)
    print_sql_string(sql, (firstname, lastname,userroleid,hashed_password))
    try:
        # Try executing the SQL and get from the database

        cur.execute(sql,(firstname, lastname,userroleid,hashed_password))
        
        # r = cur.fetchone()
        r=[]
        conn.commit()                   # Commit the transaction
        print("return val is:")
        print(r)
        cur.close()                     # Close the cursor
        conn.close()                    # Close the connection to the db
        return r
    except:
        # If there were any errors, return a NULL row printing an error to the debug
        print("Unexpected error adding a user:", sys.exc_info()[0])
        cur.close()                     # Close the cursor
        conn.close()                    # Close the connection to the db
        raise

##  Delete
###     delete_user(userid)
def delete_user(userid):
    """
    Remove a user from your system
    """
    # Data validation checks are assumed to have been done in route processing
    conn = database_connect()
    if(conn is None):
        return None
    cur = conn.cursor()
    try:
        # Try executing the SQL and get from the database
        sql = f"""
        DELETE
        FROM opaltravel.users
        WHERE userid = {userid};
        """

        cur.execute(sql,())
        conn.commit()                   # Commit the transaction
        r = []
        # r = cur.fetchone()
        # print("return val is:")
        # print(r)
        cur.close()                     # Close the cursor
        conn.close()                    # Close the connection to the db
        return r
    except:
        # If there were any errors, return a NULL row printing an error to the debug
        print("Unexpected error deleting  user with id ",userid, sys.exc_info()[0])
        cur.close()                     # Close the cursor
        conn.close()                    # Close the connection to the db
        raise

def list_traveltimes():
    conn = database_connect()
    if conn is None:
        return None
    cur = conn.cursor()
    try:
        sql = "SELECT * FROM opaltravel.TravelTimes"
        return dictfetchall(cur, sql)
    except:
        print("Error fetching data from TravelTimes table:", sys.exc_info()[0])
    finally:
        cur.close()
        conn.close()
    return None

def search_paths_bystops(stop_number):
    conn = database_connect()
    if conn is None:
        return None
    cur = conn.cursor()
    try:
        sql = "SELECT * FROM opaltravel.TravelTimes WHERE stopstraversed = %s"
        return dictfetchall(cur, sql, (stop_number,))
    except:
        print("Error searching paths by stops:", sys.exc_info()[0])
    finally:
        cur.close()
        conn.close()
    return None

def insert_travel_time(startstationid, endstationid, expectedtraveltimeseconds, stopstraversed, triplegs, coordinatemaplen):
    conn = database_connect()
    if conn is None:
        return False
    cur = conn.cursor()
    try:
        sql = """INSERT INTO opaltravel.TravelTimes (startstationid, endstationid, expectedtraveltimeseconds, stopstraversed, triplegs, coordinatemaplen) 
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        cur.execute(sql, (startstationid, endstationid, expectedtraveltimeseconds, stopstraversed, triplegs, coordinatemaplen))
        conn.commit()
        return True
    except Exception as e:
        print("Error inserting travel time:", sys.exc_info()[0])
        print("Detailed error:", str(e))
        return False
    finally:
        cur.close()
        conn.close()
        
def list_station_ids():
    conn = database_connect()
    if conn is None:
        return None
    cur = conn.cursor()
    try:
        sql = "SELECT stationid FROM opaltravel.stations"
        cur.execute(sql)
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print("Error fetching station IDs:", sys.exc_info()[0])
        #print("This is for test")
        #print("Detailed error:", str(e))
    finally:
        cur.close()
        conn.close()
    return None

def delete_travel_time(startstationid, endstationid):
    conn = database_connect()
    if conn is None:
        return False
    cur = conn.cursor()
    try:
        sql = """DELETE FROM opaltravel.TravelTimes WHERE startstationid=%s AND endstationid=%s"""
        cur.execute(sql, (startstationid, endstationid))
        conn.commit()
        return True
    except:
        print("Error deleting travel time:", sys.exc_info()[0])
        return False
    finally:
        cur.close()
        conn.close()

def get_travel_time(startstationid, endstationid):
    conn = database_connect()
    if conn is None:
        return None
    cur = conn.cursor()
    try:
        sql = """SELECT * FROM opaltravel.TravelTimes WHERE startstationid=%s AND endstationid=%s"""
        cur.execute(sql, (startstationid, endstationid))
        result = cur.fetchone()
        if result:
            column_names = [desc[0].decode('utf-8') if isinstance(desc[0], bytes) else desc[0] for desc in cur.description]
            result_dict = dict(zip(column_names, result))
            return result_dict
        else:
            return None
    except Exception as e:
        print("Error getting travel time:", sys.exc_info()[0])
        print("Detailed error:", str(e))
        return None
    finally:
        cur.close()
        conn.close()


def update_travel_time_in_db(startstationid, endstationid, expectedtraveltimeseconds, stopstraversed, triplegs, coordinatemaplen):
    conn = database_connect()
    if conn is None:
        print("Error connecting to the database.")
        return False
    
    cur = conn.cursor()
    
    try:
        sql = """
            UPDATE opaltravel.TravelTimes 
            SET expectedtraveltimeseconds=%s, stopstraversed=%s, triplegs=%s, coordinatemaplen=%s 
            WHERE startstationid=%s AND endstationid=%s
        """
        params = (expectedtraveltimeseconds, stopstraversed, triplegs, coordinatemaplen, startstationid, endstationid)
        
        # Execute the UPDATE statement
        cur.execute(sql, params)
        
        # Committing the changes
        conn.commit()

        # Use rowcount to determine if rows were affected
        if cur.rowcount > 0:
            return True
        return False

    except Exception as e:
        print("Error updating travel time:", e)
        return False
    finally:
        cur.close()
        conn.close()

def get_max_travel_time_per_startstation():
    conn = database_connect()
    if conn is None:
        return None
    
    cur = conn.cursor()
    results = []
    try:
        sql = """
            WITH MaxTravel AS (
                SELECT startstationid, 
                       endstationid,
                       expectedtraveltimeseconds,
                       RANK() OVER(PARTITION BY startstationid ORDER BY expectedtraveltimeseconds DESC) as rnk
                FROM opaltravel.TravelTimes
            )
            SELECT startstationid, endstationid, expectedtraveltimeseconds
            FROM MaxTravel
            WHERE rnk = 1;
        """
        cur.execute(sql)
        results = cur.fetchall()
        print("the results database return: "+str(results))
    except:
        print("Error fetching max travel time report:", sys.exc_info()[0])
    finally:
        cur.close()
        conn.close()
    return results

def get_max_travel_time_per_endstation():
    conn = database_connect()
    if conn is None:
        return None
    
    cur = conn.cursor()
    results = []
    try:
        sql = """
            WITH MaxTravel AS (
                SELECT endstationid, 
                       startstationid,
                       expectedtraveltimeseconds,
                       RANK() OVER(PARTITION BY endstationid ORDER BY expectedtraveltimeseconds DESC) as rnk
                FROM opaltravel.TravelTimes
            )
            SELECT endstationid, startstationid, expectedtraveltimeseconds
            FROM MaxTravel
            WHERE rnk = 1;
        """
        cur.execute(sql)
        results = cur.fetchall()
        print("the results database return: "+str(results))
    except:
        print("Error fetching max travel time report:", sys.exc_info()[0])
    finally:
        cur.close()
        conn.close()
    return results

def sign_password(password):
    salt = os.urandom(blake2b.SALT_SIZE)
    h = blake2b(salt=salt, key=routes.secret_key.encode())
    h.update(password.encode())
    return f'{salt.hex()}${h.hexdigest()}'

def check_password(password, signed_password):
    salt, hashed_password = signed_password.split("$")
    h = blake2b(salt=bytes.fromhex(salt), key=routes.secret_key.encode())
    h.update(password.encode())
    #print("Is the secret key the same? "+str(routes.secret_key == 'SoMeSeCrEtKeYhErE'))
    #print("secret key is "+routes.secret_key)
    #print("signed_password is "+signed_password)
    #print("password is "+password)
    #print("salt is "+salt)
    #print("h is "+h.hexdigest())
    #print("hashed_password is "+hashed_password)
    return compare_digest(h.hexdigest(),hashed_password)