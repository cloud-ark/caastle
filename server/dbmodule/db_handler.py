import sqlite3
from os.path import expanduser
import yaml

from common import constants

home_dir = expanduser("~")

APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)
DBFILE = APP_STORE_PATH + "/cld.sqlite"

RESOURCE_NAME = 2
RESOURCE_TYPE = 3
RESOURCE_FILTERED_DESCRIPTION = 6

ENV_NAME = 1
ENV_STATUS = 2
ENV_DEFINITION = 3
ENV_OUTPUT_CONFIG = 4

APP_ID = 0
APP_NAME = 1
APP_LOCATION = 2
APP_VERSION = 3
APP_DEP_TARGET = 4
APP_STATUS = 5
APP_OUTPUT_CONFIG = 6
APP_ENV_ID = 7

class DBHandler(object):
    def __init__(self):
        self.conn = sqlite3.connect(DBFILE)

        first_time = True
        if first_time:
            self.setup()
            first_time = False

    def setup(self):
        conn = sqlite3.connect(DBFILE)

        environment_table = ('''CREATE TABLE if not exists environment
                             (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                             NAME TEXT NOT NULL,
                             STATUS CHAR(200),
                             ENV_DEFINITION TEXT NOT NULL,
                             OUTPUT_CONFIG TEXT);''')
        conn.execute(environment_table)
        
        app_table = ('''CREATE TABLE if not exists app
                     (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                      NAME TEXT NOT NULL,
                      LOCATION TEXT NOT NULL,
                      VERSION TEXT NOT NULL,
                      DEP_TARGET TEXT NOT NULL,
                      STATUS CHAR(200),
                      OUTPUT_CONFIG TEXT,
                      ENV_ID INTEGER);''')
        conn.execute(app_table)
        
        conn.execute('''CREATE TABLE if not exists resource_stack
                    (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                     NAME TEXT NOT NULL,
                     STACK_DEFINITION TEXT NOT NULL);''')
    
        conn.execute('''CREATE TABLE if not exists resource
                    (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                     ENV_ID INTEGER,
                     CLOUD_RESOURCE_ID TEXT NOT NULL,
                     TYPE CHAR(100) NOT NULL,
                     STATUS CHAR(200),
                     INPUT_CONFIG TEXT,
                     FILTERED_DESCRIPTION TEXT,
                     DETAILED_DESCRIPTION TEXT
                     );''')
        conn.commit()
        return conn

    def _execute_cmd(self, cmd, params):
        conn = sqlite3.connect(DBFILE)
        cursor = conn.cursor()
        cursor.execute(cmd, params)
        conn.commit()
        return cursor

    # Actions on app table
    def add_app(self, app_name, app_location, app_version, cloud, env_id):
        cmd = ('INSERT INTO app(NAME, LOCATION, VERSION, DEP_TARGET, ENV_ID) VALUES(?, ?, ?, ?, ?)') 
        params = [app_name, app_location, app_version, cloud, env_id]
        cursor = self._execute_cmd(cmd, params)
        return cursor.lastrowid

    def get_app(self, app_id):
        cmd = ("select * from app where id=?")
        params = [app_id]
        cursor = self._execute_cmd(cmd, params)
        row = cursor.fetchone()
        return row

    def update_app(self, app_id, status='', output_config=''):
        cmd = ("update app set status=?, output_config=? where ID=?")
        params = [status, output_config, app_id]
        self._execute_cmd(cmd, params)

    def delete_app(self, app_id):
        cmd = ("delete from app where ID=?")
        params = [app_id]
        self._execute_cmd(cmd, params)

    def get_apps(self):
        cursor = self.conn.cursor()
        cursor.execute("select * from app")
        rows = cursor.fetchall()
        return rows
    
    def get_apps_on_environment(self, env_id):
        cmd = ("select * from app where ENV_ID=?")
        params = [env_id]
        cursor = self._execute_cmd(cmd, params)
        rows = cursor.fetchall()
        return rows

    # Actions on environment table
    def add_environment(self, env_name, env_obj, env_version_stamp):
        env_definition = str(env_obj)
        env_output_config = {}
        env_output_config['env_version_stamp'] = env_version_stamp
        cursor = self.conn.cursor()
        cmd = ('INSERT INTO environment(NAME, STATUS, ENV_DEFINITION, OUTPUT_CONFIG) VALUES(?, ?, ?, ?)')
        params = [env_name, 'creating', env_definition, str(env_output_config)]
        cursor = self._execute_cmd(cmd, params)
        env_id = cursor.lastrowid
        return env_id

    def update_environment_status(self, env_id, status=''):
        cmd = ("update environment set status=? where ID=?")
        params = [status, env_id]
        self._execute_cmd(cmd, params)

    def update_environment(self, env_id, status='', output_config=''):
        cmd = ("update environment set status=?, output_config=? where ID=?")
        params = [status, output_config, env_id]
        self._execute_cmd(cmd, params)

    def get_environments(self):
        cursor = self.conn.cursor()
        cursor.execute("select * from environment")
        rows = cursor.fetchall()
        return rows
    
    def get_environment(self, env_id):
        cmd = ("select * from environment where id=?")
        params = [env_id]
        cursor = self._execute_cmd(cmd, params)
        row = cursor.fetchone()
        return row

    def delete_environment(self, env_id):
        cmd = ("delete from environment where ID=?")
        params = [env_id]
        cursor = self._execute_cmd(cmd, params)

    # Actions on resource_stack table
    def get_resource_stacks(self):
        cursor = self.conn.cursor()
        cursor.execute("select * from resource_stack")
        rows = cursor.fetchall()
        return rows

    def add_resource_stack(self, stack_obj):        
        name = str(stack_obj['resource_stack']['name'])
        stack_definition = str(stack_obj['resource_stack'])
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO resource_stack(NAME, STACK_DEFINITION) VALUES(?, ?)', [name, stack_definition])
        self.conn.commit()
        stack_id = cursor.lastrowid
        return stack_id
    
    def get_resource_stack(self, stack_id):
        cursor = self.conn.cursor()
        cursor.execute("select * from resource_stack where ID=?",[stack_id])
        row = cursor.fetchone()
        return row

    def delete_resource_stack(self, stack_id):
        cursor = self.conn.cursor()
        cursor.execute("delete from resource_stack where ID=?",[stack_id])
        self.conn.commit()

    # Actions on resource table
    def get_resources(self):
        cursor = self.conn.cursor()
        cursor.execute("select * from resource")
        rows = cursor.fetchall()
        return rows

    def add_resource(self, env_id, instance_id, type, status):
        cmd = ('INSERT INTO resource(ENV_ID, CLOUD_RESOURCE_ID, TYPE, STATUS) VALUES(?,?,?,?)')
        params = [env_id, instance_id, type, status]
        cursor = self._execute_cmd(cmd, params)
        resource_id = cursor.lastrowid
        return resource_id

    def add_resource_prev(self, request_obj):
        name = str(request_obj['name'])
        type = str(request_obj['resource_type'])
        status = constants.CREATION_REQUEST_RECEIVED
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO resource(NAME, TYPE, STATUS) VALUES(?,?,?)', [name, type, status])
        self.conn.commit()
        resource_id = cursor.lastrowid
        return resource_id

    def get_resource(self, resource_id):
        cursor = self.conn.cursor()
        cursor.execute("select * from resource where ID=?",[resource_id])
        row = cursor.fetchone()
        return row

    def get_resources_for_environment(self, env_id):
        command = "select * from resource where env_id=?"
        params = [env_id]
        cursor = self._execute_cmd(command, params)
        rows = cursor.fetchall()
        return rows

    def update_resource(self, resource_id, status='', filtered_description=None, detailed_description=''):
        cmd = ("update resource set status=?, filtered_description=?, detailed_description=? where ID=?")
        params = [status, filtered_description, detailed_description, resource_id]
        cursor = self._execute_cmd(cmd, params)
        
    def update_resource_for_environment(self, env_id, status='', filtered_description=None, detailed_description=''):
        cmd = ("update resource set status=? where ENV_ID=?")
        params = [status, env_id]
        cursor = self._execute_cmd(cmd, params)
        resource_id = cursor.lastrowid
        return resource_id

    def delete_resource(self, resource_id):
        cmd = ("delete from resource where ID=?")
        params = [resource_id]
        cursor = self._execute_cmd(cmd, params)