import sqlite3
from pathlib import Path


def database_connect(name):
    path = Path(name)
    if path.is_file():
        try:
            connection = sqlite3.connect(name)
        except sqlite3.OperationalError as error:
            print("ERROR: %s" % error)
            return None
        return connection
    else:
        return None


def database_disconnect(connection):
    connection.close()


def database_initialize(name):
    path = Path(name)
    if path.is_file():
        print("WARNING: database %s already exists. Cowardly refusing action." % name)
    else:
        create_statement_file_path = Path("lib/initialize-image-catalog.sql")
        if create_statement_file_path.is_file():
            db_init_file = open("lib/initialize-image-catalog.sql")
            create_statement = db_init_file.read()
            db_init_file.close()
        else:
            raise SystemError("Template lib/initialize-image-catalog.sql not found")
        # print(create_statement)
        try:
            connection = sqlite3.connect(name)
        except sqlite3.OperationalError as error:
            print("ERROR: %s" % error)
        database_cursor = connection.cursor()
        try:
            database_cursor.execute(create_statement)
        except Exception as error:
            print('ERROR: create table failed with the following error "%s"' % error)

        connection.close()
        print("New database created under %s" % name)


def db_get_last_checksum(connection, distribution, release):
    # sqlite error handling not yet implemented !!!
    database_cursor = connection.cursor()
    database_cursor.execute("SELECT checksum FROM image_catalog WHERE distribution_name = '%s' AND distribution_release = '%s' ORDER BY id DESC LIMIT 1" % (distribution, release))
    row = database_cursor.fetchone()

    if row is None:
        # print("no previous entries found")
        last_checksum = "sha256:none"
    else:
        last_checksum = row[0]

    database_cursor.close()
    return last_checksum


def write_catalog_entry(connection, update):
    database_cursor = connection.cursor()
    database_cursor.execute("INSERT INTO image_catalog (name, release_date, version, distribution_name, distribution_release, url, checksum) VALUES (?,?,?,?,?,?,?)",
                            (update['name'], update['release_date'], update['version'], update['distribution_name'], update['distribution_release'], update['url'], update['checksum']))
    connection.commit()
    database_cursor.close()
    # TODO: return sucess or failure

    return None


def read_release_from_catalog(connection, distribution, release):
    database_cursor = connection.cursor()
    database_cursor.execute("SELECT version,checksum,url,release_date FROM (SELECT * FROM image_catalog WHERE distribution_name = '%s' AND distribution_release = '%s' ORDER BY id DESC LIMIT 2) ORDER BY ID" % (distribution, release))

    image_catalog = {}
    image_catalog['versions'] = {}

    for image in database_cursor.fetchall():
        version = image[0]
        image_catalog['versions'][version] = {}
        image_catalog['versions'][version]['checksum'] = image[1]
        image_catalog['versions'][version]['url'] = image[2]
        image_catalog['versions'][version]['release_date'] = image[3]

    return image_catalog