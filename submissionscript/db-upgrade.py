import os
import re
import logging
import sys
import time

import mysql.connector
import socket

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

file_path = sys.argv[1]
migrationPattern = re.compile(r"^(\d+)\.?[\w\s]+\.sql$")

# due to a race condition (mysql is up but not quiet ready to accept the connections)
# add an additional check for socket connectivity.
connectionEnabled = False
a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
for i in range(10):
    if a_socket.connect_ex((os.environ.get("MYSQL_HOST"), 3306)) == 0:
        logger.debug("got connectivity to mysql")
        connectionEnabled = True
        break
    logger.debug("could not connect to mysql [%s:3306], zzz", os.environ.get("MYSQL_HOST"))
    time.sleep(5)
a_socket.close()
if connectionEnabled is False:
    logger.error("could not connect to mysql server after 10 tries")
    exit(3)

# we have a socket connection to db, try to auth
db_connection = mysql.connector.connect(
    host=sys.argv[3],
    user=sys.argv[2],
    passwd=sys.argv[5],
    database=sys.argv[4]
)
db_cursor = db_connection.cursor(dictionary=True)


def load_migration_files():
    """
    Loads migration file from a given folder based on their regex mask
    :return: dictionary composed of version=>filename
    """
    file_list: dict[str, str] = {}
    for (_, _, filenames) in os.walk(file_path):
        for f in filenames:
            match = migrationPattern.search(f)
            # skip if our file doesn't match regex
            if match is None:
                continue

            file_list[match.group(1)] = f
    return file_list


def get_latest_version():
    """
    Returns the maximum version fetched from the version table
    :rtype: int
    """
    db_cursor.execute("SELECT max(version) as version FROM versionTable;")
    result_version = db_cursor.fetchone()
    return result_version["version"]


# load migration files and check that the resulting list is not empty
migration_files = load_migration_files()
if len(migration_files) == 0:
    logger.error("could not find any files matching defined regex. exiting")
    exit(1)

# obtain the latest version and begin comparison
latest_version = get_latest_version()
for version in sorted(migration_files):
    # skip if it has already been executed in the past
    if int(version) <= latest_version:
        logger.debug("skipping version %s", version)
        continue

    try:
        with open(file_path + "/" + migration_files[version]) as sql_file:
            iterator = db_cursor.execute(sql_file.read(), multi=True)
            try:
                for res in iterator:
                    logger.debug("executing query: [%s], affected %d rows", res, res.rowcount)
            except StopIteration:  # this only happens in container.
                pass
            iterator.close()

            db_cursor.execute("INSERT INTO versionTable (version) VALUES (%s)", (int(version),))
            db_connection.commit()
            latest_version = int(version)
    except mysql.connector.Error as error:
        logger.error("failed to execute query [%s], rolling back", error)
        try:  # empty exception handler in case rollback fails
            db_connection.rollback()
        except:
            # should not happen, but just in case
            logger.error("could not roll back")
            pass
        exit(2)

logger.info("finished migration scripts. Latest version is %d", latest_version)
db_cursor.close()
db_connection.close()
