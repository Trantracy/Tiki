import os.path

from flask import Flask, render_template, request, redirect
from bs4 import BeautifulSoup
from collections import deque
import requests
import sqlite3
import pandas as pd
import time


app = Flask(__name__)

if not os.path.isfile('tiki.db'):
    TIKI_URL = 'https://tiki.vn'

    #Connect to database
    conn = sqlite3.connect('tiki.db')
    #point to database
    cur = conn.cursor()

    def create_categories_table():
        """ Create to database table AUTOINCREMENT: everytime request increase ID+1"""
        query = """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255),
                url TEXT, 
                parent_id INT, 
                create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        try:
            cur.execute(query)
        except Exception as err:
        # Define the error.
            print('ERROR BY CREATE TABLE', err)

    create_categories_table()

    def select_all():
        return cur.execute('SELECT * FROM categories;').fetchall()

    def delete_all():
        return cur.execute('DELETE FROM categories;')

    class Category:
        def __init__(self, cat_id, name, url, parent_id):
            self.cat_id = cat_id
            self.name = name
            self.url = url
            self.parent_id = parent_id

        def __repr__(self):
            return "ID: {}, Name: {}, URL: {}, Parent_id: {}".format(self.cat_id, self.name, self.url, self.parent_id)

        def save_into_db(self):
            # Connect to the database SQL
            query = """
                INSERT INTO categories (name, url, parent_id)
                VALUES (?, ?, ?);
            """
            val = (self.name, self.url, self.parent_id)
            try:
                cur.execute(query, val)
                self.cat_id = cur.lastrowid
            except Exception as err:
                print('ERROR BY INSERT:', err)
            conn.commit()
            
    def get_url(url):
        # To avoid to be blocked IP
        time.sleep(1)
        try:
            response = requests.get(url).text
            response = BeautifulSoup(response, 'html.parser')
            return response
        except Exception as err:
                print('ERROR BY REQUEST:', err)

    def get_main_categories(save_db):
        # Get the parent categories
        save_db = False
        soup = get_url(TIKI_URL)

        result = []
        for a in soup.findAll('a', {'class':'MenuItem__MenuLink-tii3xq-1 efuIbv'}):
            cat_id = None
            name = a.find('span', {'class':'text'}).text
            url = a['href']
            parent_id = None

            cat = Category(cat_id, name, url, parent_id)
            if save_db:
                cat.save_into_db()
            result.append(cat)
        return result

    main_categories = get_main_categories(save_db=True)

    def get_sub_categories(category, save_db=False):
        # Get the sub cat
        name = category.name.text
        url = category.url
        result = []

        try:
            soup = get_url(url)
            div_containers = soup.findAll('div', {'class':'list-group-item is-child'})
            for div in div_containers:
                sub_id = None
                sub_name = div.a.text
                sub_url = 'http://tiki.vn' + div.a['href']
                sub_parent_id = category.cat_id

                sub = Category(sub_id, sub_name, sub_url, sub_parent_id)
                if save_db:
                    sub.save_into_db()
                result.append(sub)
        except Exception as err:
            print('ERROR BY GET SUB CATEGORIES:', err)

        return result

    # a list from collections import deque
    de = deque([1, 2, 3])
    de.extend([4, 5])
    de.append(6)

    def get_all_categories(main_categories):
        de = deque(main_categories)
        count = 0

        while de:
            parent_cat = de.popleft()
            sub_cats = get_sub_categories(parent_cat, save_db=True)
            print(sub_cats)
            de.extend(sub_cats)
            count += 1

            if count % 100 == 0:
                print(count, 'times')

        
    get_all_categories(main_categories)
else:
    conn = sqlite3.connect('tiki.db')
    cur = conn.cursor()

pd.set_option('colheader_justify', 'center')
df = pd.read_sql_query("""
                        SELECT p.id, p.name, p.url, p.parent_id, c.name AS Parent 
                        FROM categories p 
                        LEFT JOIN categories c ON p.parent_id=c.id
                        """, conn)

print(df)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', data=df.to_html())

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8000, debug=True)
 