#  This file is part of Gazee.
#
#  Gazee is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Gazee is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Gazee.  If not, see <http://www.gnu.org/licenses/>.

import os
import sqlite3
import configparser
import logging

from pathlib import Path
from gazee.gazee import Gazee
from gazee.comicscan import ComicScanner
import gazee.authmech

__version__ = '0.0.1'
__all__ = ['Gazee', 'ComicScanner']

FULL_PATH = ""
DB_NAME = 'gazee.db'
DATA_DIR = 'data'
TEMP_DIR = 'tmp'
PIDFILE = '/tmp/gazee.pid'

if not os.path.exists(TEMP_DIR):
    os.makedirs(os.path.abspath(TEMP_DIR))

if not os.path.exists(DATA_DIR):
    os.makedirs(os.path.abspath(DATA_DIR))

if not os.path.exists(os.path.join(DATA_DIR, 'sessions')):
    os.makedirs(os.path.abspath(os.path.join(DATA_DIR, 'sessions')))

logging.basicConfig(level=logging.DEBUG, filename=os.path.join(gazee.DATA_DIR, 'gazee.log'))
logger = logging.getLogger(__name__)

if not os.path.exists(os.path.join(DATA_DIR, 'app.ini')):
    with open(os.path.join(DATA_DIR, 'app.ini'), 'a') as cf:
        cf.write("[GLOBAL]\n")
        cf.write("port = 4242\n")
        cf.write("comic_path =\n")
        cf.write("comic_scan_interval = 60\n")
        cf.write("comics_per_page = 15\n")
        cf.write("mylar_db =\n")
        cf.write("ssl_key =\n")
        cf.write("ssl_cert =\n")
        cf.write("web_text_color = FFFFFF\n")
        cf.write("main_color = 757575\n")
        cf.write("accent_color = bdbdbd\n")
    cf.close()

config = configparser.ConfigParser()
config.read(os.path.join(DATA_DIR, 'app.ini'))

PORT = int(config['GLOBAL']['PORT'])
COMIC_PATH = config['GLOBAL']['COMIC_PATH']
COMIC_SCAN_INTERVAL = config['GLOBAL']['COMIC_SCAN_INTERVAL']
COMICS_PER_PAGE = int(config['GLOBAL']['COMICS_PER_PAGE'])
MYLAR_DB = config['GLOBAL']['MYLAR_DB']
SSL_KEY = config['GLOBAL']['SSL_KEY']
SSL_CERT = config['GLOBAL']['SSL_CERT']
WEB_TEXT_COLOR = config['GLOBAL']['WEB_TEXT_COLOR']
MAIN_COLOR = config['GLOBAL']['MAIN_COLOR']
ACCENT_COLOR = config['GLOBAL']['ACCENT_COLOR']
ARGS = []
THUMB_SIZE = 400, 300

# Declare DB variables, such as table names and field names
# This is mostly so the names are in a central area for later reference.

# Directories table, holds all actual directories full paths. We iterate over these in comicscan for their contents and add those to the below Directory Names table with the associated key.
ALL_DIRS = "all_directories"
FULL_DIR_PATH = "full_dir_path"
KEY = "key"

# Directory Names. This will hold the actual names of directories and their associated parent keys.
DIR_NAMES = "dir_names"
NICE_NAME = "nice_name"
DIR_IMAGE = "dir_image"
PARENT_KEY = "parent_key"

# Comics table and various attributes we associate with them.
ALL_COMICS = "all_comics"
COMIC_IMAGE = "image"
COMIC_NAME = "name"
COMIC_NUMBER = "issue"
COMIC_VOLUME = "volume"
COMIC_SUMMARY = "summary"
COMIC_FULL_PATH = "path"
INSERT_DATE = "date"

# Users Table and various attributes.
USERS = "USERS"
USERNAME = "username"
PASSWORD = "password"
TYPE = "type"

# Create DB if it doesn't already exist.
db = Path(os.path.join(DATA_DIR, DB_NAME))
if not db.is_file():
    connection = sqlite3.connect(str(db))
    c = connection.cursor()

    # Create the Directories table.
    c.execute('CREATE TABLE {tn} ({nf} {ft} PRIMARY KEY)'.format(tn=ALL_DIRS, nf=KEY, ft="INTEGER"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=ALL_DIRS, cn=FULL_DIR_PATH, ft="TEXT"))

    # Create the Directory table.
    c.execute('CREATE TABLE {tn} ({nf} {ft})'.format(tn=DIR_NAMES, nf=NICE_NAME, ft="TEXT"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=DIR_NAMES, cn=DIR_IMAGE, ft="TEXT"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=DIR_NAMES, cn=PARENT_KEY, ft="INTEGER"))

    # Create Comics table and necessary columns.
    c.execute('CREATE TABLE {tn} ({nf} {ft} PRIMARY KEY)'.format(tn=ALL_COMICS, nf=KEY, ft="INTEGER"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=ALL_COMICS, cn=COMIC_NAME, ft="TEXT"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=ALL_COMICS, cn=COMIC_IMAGE, ft="TEXT"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=ALL_COMICS, cn=COMIC_NUMBER, ft="INTEGER"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=ALL_COMICS, cn=COMIC_VOLUME, ft="INTEGER"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=ALL_COMICS, cn=COMIC_SUMMARY, ft="TEXT"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=ALL_COMICS, cn=COMIC_FULL_PATH, ft="TEXT"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=ALL_COMICS, cn=PARENT_KEY, ft="INTEGER"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}'".format(tn=ALL_COMICS, cn=INSERT_DATE))

    # Create Users colume and necessary columns.
    c.execute('CREATE TABLE {tn} ({nf} {ft})'.format(tn=USERS, nf=USERNAME, ft="TEXT"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=USERS, cn=PASSWORD, ft="TEXT"))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ft}".format(tn=USERS, cn=TYPE, ft="TEXT"))

    connection.commit()
    connection.close()
    logging.info("DB Schema Created")

# Insert Admin user into DB if they aren't already there.
connection = sqlite3.connect(str(db))
c = connection.cursor()

c.execute('SELECT ({cn}) FROM {tn}'.format(cn=USERNAME, tn=USERS))
all_users = c.fetchall()

# Since queries return lists of tuples, we have to iterate those. We can use list comprehension here to iterate through the items in the first element of each tuple in the list. If the adminCheck variable is larger than 0, the admin has already been created, or something has gone horribly wrong.
adminCheck = [tup[0] for tup in all_users]

if len(adminCheck) == 0:
    c.execute('INSERT INTO {tn} ({cn1}, {cn2}, {cn3}) VALUES ("admin", "87f69abe62021d9ab8497e052c65ee79ca6705169916b930ea3e6979a0555c4d", "admin")'.format(tn=USERS, cn1=USERNAME, cn2=PASSWORD, cn3=TYPE))
    logging.info("Admin inserted into DB")

connection.commit()
connection.close()
