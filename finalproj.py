import sqlite3
from pandas import DataFrame
import requests
import json
import plotly
import plotly.graph_objs as go
from bs4 import BeautifulSoup
import statistics
import re
import secrets
import emoji
import webbrowser

# -*- coding: UTF-8 -*-

print("Loading program...")

CACHE_FNAME = 'finalproj-cache.json'
DBNAME = 'books.db'
BASE_URL = 'https://www.goodreads.com/'
GOODREADS_KEY = secrets.GOODREADS_KEY
GOOGLE_KEY = secrets.google_places_key
MAPBOX_TOKEN = secrets.MAPBOX_TOKEN
place_base_url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?'

###initialize the database tables if not exist###
def init_db():

  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()

  cur.execute('''CREATE TABLE IF NOT EXISTS 'Books' (
    'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
    'GroupId' TEXT,
    'ISBN' TEXT,
    'Title' TEXT,
    'SettingLocation' TEXT,
    'KindlePrice' REAL,
    'AmazonLink' TEXT,
    'AverageRating' REAL,
    'ReviewCount' INTEGER,
    UNIQUE (Title)
    );''')

  cur.execute('''CREATE TABLE IF NOT EXISTS 'Settings' (
      'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
      'Book' INTEGER,
      'Location' TEXT,
      'LocationLat' INTEGER,
      'LocationLon' INTEGER,
      FOREIGN KEY(Book) REFERENCES Books(Id)
      );''')

  conn.commit()
  return None

init_db()

###class definition for Books that will be loaded into the databse###
class Book():
    def __init__(self, groupid, isbn, title, settings, kindle_price, amazon_link):
        self.groupid = groupid
        if isbn != None:
          self.isbn = isbn
        else:
          self.isbn = None
        self.title = title
        if settings != None:
          self.settings = settings
        else:
          self.settings = None
        if kindle_price != None:
          self.kindle_price = kindle_price
        else:
          self.kindle_price = None
        self.amazon_link = amazon_link

        review_json = get_book_reviews(isbn)

        if review_json != None:
          reviews_books = review_json['books']
          for elem in reviews_books:
            self.average_rating = elem['average_rating']
            self.reviews_count = elem['reviews_count']
        else:
          self.average_rating = None
          self.reviews_count = None

    def __str__(self):
        return self.title

###see if cache file exists, if not, create one###
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

def get_unique_key(url):
  return url

###makes request using cache file###
def make_request_using_cache(url,header=None):
    unique_ident = get_unique_key(url)
    if unique_ident in CACHE_DICTION:
        # print("Getting cached data...")
        return CACHE_DICTION[unique_ident]
    else:
        # print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(url)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]

###scrapes Goodreads Group page for links to individual books###
def get_books_from_group(group_id):
  group_url_piece = 'group/bookshelf/'
  ###uses Goodreads Group ID number to access group page###
  group_id_url_piece = str(group_id)
  read_shelf_url_piece = '?order=d&per_page=30&shelf=read&sort=date_added&view=main'
  group_read_url = BASE_URL+group_url_piece+group_id_url_piece+read_shelf_url_piece
  header = {'User-agent': 'Mozilla/5.0'}

  books_list = []

  ###scrapes 'read' bookshelf of group for page data###
  bookshelf_txt = make_request_using_cache(group_read_url,header)
  bookshelf_soup = BeautifulSoup(bookshelf_txt, 'html.parser')
  book_links = []

  book_nav = bookshelf_soup.find('div',{'style':'float: left'})
  ###test to see if bookshelf is only one page, or multiple pages###
  ###if multiple pages, scrape each page to get detail page links for every book in bookshelf###
  if book_nav != None:
    bookshelf_table = bookshelf_soup.find(id='groupBooks')
    books_cell = bookshelf_table.find_all("td",{"width":'30%'})
    for elem in books_cell:
      book_url = elem.find('a')['href']
      book_links.append(book_url)

    book_nav_links = book_nav.find_all('a')
    for elem in book_nav_links:
      book_nav_url = elem['href']
      book_nav_txt = make_request_using_cache(BASE_URL+str(book_nav_url),header)
      book_nav_soup = BeautifulSoup(book_nav_txt, 'html.parser')
      bookshelf_table = book_nav_soup.find(id='groupBooks')
      books_cell = bookshelf_table.find_all("td",{"width":'30%'})
      for elem in books_cell:
        book_url = elem.find('a')['href']
        book_links.append(book_url)

  ###else - if one page, get links to detail pages for all books in bookshelf####
  else:
    bookshelf_table = bookshelf_soup.find(id='groupBooks')
    books_cell = bookshelf_table.find_all("td",{"width":'30%'})
    for elem in books_cell:
      book_url = elem.find('a')['href']
      book_links.append(book_url)

  ###return group id and list of detail page links for each book###
  return [group_id,book_links]

###uses list of detail page links to get individual book data###
def get_book_info(list_w_group_id_book_links):
  group_id = list_w_group_id_book_links[0]
  book_links = list_w_group_id_book_links[1]
  book_insts = []
  for book_link in book_links:
    group_id = group_id
    book_url_piece = book_link
    header = {'User-agent': 'Mozilla/5.0'}
    book_url = BASE_URL+book_url_piece
    book_txt = make_request_using_cache(book_url,header)
    book_soup = BeautifulSoup(book_txt, 'html.parser')

    ###scrapes detail page for book title###
    title = book_soup.find(id='bookTitle').text.strip()

    ###scrapes detail page for book Kindle price###
    buy_buttons = book_soup.find(class_='buyButtonBar left')
    amazon_buy = buy_buttons.find_all('li')[0]
    try:
      amazon_link = amazon_buy.find('a')['data-amazon-url']
      kindle_price_txt = amazon_buy.text.replace('\n','')
      kindle_price = float(kindle_price_txt.split('$')[1])
    except:
      kindle_price = None
      amazon_button = amazon_buy.find(class_='buttonBar')['href']
      amazon_link = BASE_URL+(amazon_button[1:])

    ###scrapes detail page for book ISBN or ASIN###
    info_box = book_soup.find(id='bookDataBox')
    info_items = info_box.find_all(class_='clearFloats')
    isbn = None
    settings = []
    setting_item = None
    for elem in info_items:
      if elem.find(class_='infoBoxRowTitle').text == 'ISBN' or elem.find(class_='infoBoxRowTitle').text == 'ISBN13' or elem.find(class_='infoBoxRowTitle').text == 'ASIN':
        isbn = elem.find(itemprop='isbn').text

    ###if book has settings listed, scrape those from page###
    try:
      setting_title = info_box.find('div', text=re.compile("setting"))
      setting_item = setting_title.find_next('div')
      setting_links = setting_item.find_all('a')
      for elem in setting_links:
        settings.append(elem.text.strip())
    except:
      settings = None

    if settings != None:
      for elem in settings:
        if elem == '…more':
          settings.remove(elem)
        elif elem == '…less':
          settings.remove(elem)

    ###crate book instances with scraped data###
    book = Book(group_id, isbn, title, settings, kindle_price, amazon_link)
    book_insts.append(book)

  ###return list of book instances###
  return book_insts

###use Goodreads API to get review information for each book###
def get_book_reviews(isbn):
  review_url = BASE_URL+'book/review_counts.json?isbns='+str(isbn)+'&key='+GOODREADS_KEY
  review_txt = make_request_using_cache(review_url)
  try:
    review_json = json.loads(review_txt)
  except:
    review_json = None

  return review_json

###use Google Places API to get location data (lat, lng) for for a single book's settings###
def get_settings_place(location_str):
  key = '&key='+GOOGLE_KEY
  inputtype = '&inputtype=textquery'
  fields = '&fields=geometry,name'
  place_params = inputtype+fields+key
  raw_query = location_str
  adj_query = "input="+raw_query.replace(" ","%20")
  place_query = place_base_url+adj_query+place_params
  place_resp = make_request_using_cache(place_query)
  place_j = json.loads(place_resp)
  if place_j['status'] != 'ZERO_RESULTS':
    candidates = place_j['candidates']
    loc_info = candidates[0]
    lat = loc_info['geometry']['location']['lat']
    lon = loc_info['geometry']['location']['lng']

    name = candidates[0]['name']

    location_dict = {}
    location_dict['name'] = name
    location_dict['lat'] = lat
    location_dict['lon'] = lon

    return location_dict
  ###if no retuls, resturn none###
  else:
    return None

###collect location data for all books in list of book instances from group###
def get_settings_dict(book_insts):
  book_settings = []
  for elem in book_insts:
    if elem.settings != None:
      for ele in elem.settings:
        book_dict = {}
        settings_api = get_settings_place(ele)
        if settings_api != None:
          book_dict[elem.isbn] = settings_api
          book_settings.append(book_dict)
  return book_settings

###load database with book info and setting info ###
def load_db(book_insts):
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()

  book_settings = get_settings_dict(book_insts)

  for elem in book_insts:
    isbn = elem.isbn
    title = elem.title
    price = elem.kindle_price
    link = elem.amazon_link
    avgrat = elem.average_rating
    revcount = elem.reviews_count
    groupid = elem.groupid
    setting_str = ""
    if elem.settings != None:
      for x in elem.settings:
        setting_str = setting_str+" "+x+" "
      settings = setting_str
    else:
      settings = None

    insertion = [None, groupid, isbn, title, settings, price, link, avgrat, revcount]

    ###load book data into Book table###
    statement = 'INSERT OR REPLACE INTO "Books" '
    statement += 'VALUES (?, ?, ?, ?, ?, ?,?,?, ?)'
    cur.execute(statement, insertion)

  if book_settings != None:
    for ele in book_settings:
      # print(ele)
      book_isbn =list(ele.keys())[0]
      if book_isbn != None:
        cur.execute("SELECT Id,ISBN FROM Books WHERE ISBN = ?", (book_isbn,))
        results_c = cur.fetchone()
        if results_c != None:
          BookID = results_c[0]
        else:
          BookID = None
        try:
          Location = ele[book_isbn]['name']
        except:
          Location = None
        LocationLat = ele[book_isbn]['lat']
        LocationLon = ele[book_isbn]['lon']
        insertion_l = [None, BookID,Location,LocationLat,LocationLon]
        try:
          ###load setting data into Settings table###
          statement_l = 'INSERT INTO "Settings"'
          statement_l += 'VALUES (?,?,?,?,?)'
          cur.execute(statement_l, insertion_l)
        except:
          pass

  conn.commit()
  return None

###plot number of reviews for all books in a line scatter graph###
def plot_review_count():
  print('Plotting number of reviews...')
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()
  cur.execute('''SELECT Title, ReviewCount FROM Books WHERE ReviewCount NOT NULL''')
  results = cur.fetchall()

  title_list = []
  for elem in results:
    title_list.append(elem[0])
  count_list = []
  for elem in results:
    count_list.append(elem[1])

  min_ct = float(min(count_list))
  max_ct = float(max(count_list))



  fig = go.Figure()
  fig.add_trace(go.Scatter(
      x=count_list,
      y=title_list,
      marker=dict(color="deeppink", size=12),
      mode="markers",
      name="Number of Reviews",
  ))

    ###################################################################################################
    ##### Add additional data points (ratings count, text reviews count -- woiuld have to add to pull from api and database first )#####################################################################
    ###################################################################################################

  fig.update_layout(title="Number of Reviews per Book",
                    xaxis_title="Number of Reviews",
                    yaxis_title="Book Title")

  fig.show()
  return None

###plot location settings for all books on a world map###
def plot_settings():
  print('Mapping Settings...')
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()

  lat_list = []
  lon_list = []
  title_list = []
  place_list = []

  cur.execute('''SELECT Books.Id, Books.Title, Settings.Book FROM Settings JOIN Books ON Settings.Book = Books.Id''')
  title_id_list = cur.fetchall()
  title_list = []
  for elem in title_id_list:
    title_list.append(elem[1])

  cur.execute('''SELECT Location FROM Settings''')
  place_list = list(sum(cur.fetchall(), ()))

  cur.execute('''SELECT LocationLat FROM Settings''')
  lat_list = list(sum(cur.fetchall(), ()))

  cur.execute('''SELECT LocationLon FROM Settings''')
  lon_list = list(sum(cur.fetchall(), ()))

  mapbox_access_token = MAPBOX_TOKEN

  lat_mean = statistics.median(lat_list)
  lng_mean = statistics.median(lon_list)

  min_lat = float(min(lat_list))
  max_lat = float(max(lat_list))
  min_lon = float(min(lon_list))
  max_lon = float(max(lon_list))

  lat_axis = [min_lat, max_lat]
  lon_axis = [max_lon, min_lon]

  fig = go.Figure(go.Scattermapbox(
   lat=lat_list,
   lon=lon_list,
   mode='markers',
   marker=go.scattermapbox.Marker(size=11),
   text=title_list,
     ))
  ###################################################
  ##### Add colors and additional text labels########
  ###################################################
  fig.update_layout(
     title = 'Where books in this group take place',
     # geo_scope='usa',
     autosize=True,
     hovermode='closest',
     mapbox=go.layout.Mapbox(
         accesstoken=mapbox_access_token,
         bearing=0,
         center=go.layout.mapbox.Center(
             lat=lat_mean,
             lon=lng_mean
         ),
         pitch=0,
         zoom=1
     ),
  )

  fig.show()

  return None

###plot average rating for all books in a bar graph by star rating (i.e. 12 books with 4 stars)###
def plot_ratings():
  print('Plotting Average Ratings...')
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()


  cur.execute('''SELECT Title FROM Books WHERE AverageRating >= 4''')
  five_rating_title = list(sum(cur.fetchall(), ()))

  cur.execute('''SELECT COUNT(*) FROM Books WHERE AverageRating >= 4''')
  five_num = cur.fetchone()[0]

  cur.execute('''SELECT Title FROM Books WHERE AverageRating >= 3 AND AverageRating < 4''')
  four_rating_title  = list(sum(cur.fetchall(), ()))

  cur.execute('''SELECT COUNT(*) FROM Books WHERE AverageRating >= 3 AND AverageRating < 4''')
  four_num = cur.fetchone()[0]

  cur.execute('''SELECT Title FROM Books WHERE AverageRating >= 2 AND AverageRating < 3''')
  three_rating_title  = list(sum(cur.fetchall(), ()))

  cur.execute('''SELECT COUNT(*) FROM Books WHERE AverageRating >= 2 AND AverageRating < 3''')
  three_num = cur.fetchone()[0]

  cur.execute('''SELECT Title FROM Books WHERE AverageRating >= 1 AND AverageRating < 2''')
  two_rating_title  = list(sum(cur.fetchall(), ()))

  cur.execute('''SELECT COUNT(*) FROM Books WHERE AverageRating >= 1 AND AverageRating < 2''')
  two_num = cur.fetchone()[0]

  cur.execute('''SELECT Title FROM Books WHERE AverageRating < 1''')
  one_rating_title  = list(sum(cur.fetchall(), ()))

  cur.execute('''SELECT COUNT(*) FROM Books WHERE AverageRating < 1''')
  one_num = cur.fetchone()[0]

  colors = ['lightslategray',] * 5

  fig = go.Figure(data=[go.Bar(
    x=['< '+'\N{white medium star}','\N{white medium star}','\N{white medium star}'+'\N{white medium star}', '\N{white medium star}'+'\N{white medium star}'+'\N{white medium star}',
       '\N{white medium star}'+'\N{white medium star}'+'\N{white medium star}'+'\N{white medium star}'],
    y=[one_num,two_num,three_num,four_num,five_num],
    marker_color=colors # marker color can be a single color value or an iterable
    )])

  fig.update_layout(title_text='Number of Books Per Star Rating')

  fig.show()

  return None

###plot average ratings for all books in a line scatter graph###
def plot_ratings_dot():
  print('Plotting Averate Ratings...')
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()

  title_list=[]
  rating_list = []

  cur.execute('''SELECT Title,AverageRating FROM Books WHERE AverageRating NOT NULL''')
  results = cur.fetchall()

  for elem in results:
    if elem[1] != None:
      title_list.append(elem[0])
      rating_list.append(elem[1])

  min_ct = float(min(rating_list))
  max_ct = float(max(rating_list))



  fig = go.Figure()
  fig.add_trace(go.Scatter(
      x=rating_list,
      y=title_list,
      marker=dict(color="deeppink", size=12),
      mode="markers",
      name="Average Ratings",
  ))

    ###################################################################################################
    ##### Add additional data points (ratings count, text reviews count -- woiuld have to add to pull from api and database first )#####################################################################
    ###################################################################################################

  fig.update_layout(title="Average Rating per Book",
                    xaxis_title="Rating (\N{white medium star} to \N{white medium star}\N{white medium star}\N{white medium star}\N{white medium star}\N{white medium star})",
                    yaxis_title="Book Title")

  fig.show()
  return None

###sort and print all books from group by the listed Kindle price###
def sort_kindle_price():
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()

  cur.execute('''SELECT Title,KindlePrice FROM Books WHERE KindlePrice NOT NULL ORDER BY KindlePrice''')
  results = cur.fetchall()
  function_results = {}
  count = 0
  header_list=['#','TITLE','PRICE']
  print("{: <3.3} {: <60.60} {: <6.6}".format(header_list[0],header_list[1],header_list[2]))
  for elem in results:
    count+=1
    function_results[count]=elem[0]
    print_count=str(count)
    print("{: <3.3} {: <60.60} {: <5.5}".format(print_count,elem[0],elem[1]))

  conn.commit()
  return function_results

###sort and print all books from group by the average rating###
def sort_average_rating():
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()

  cur.execute('''SELECT Title,AverageRating FROM Books WHERE AverageRating NOT NULL ORDER BY AverageRating''')
  results = cur.fetchall()
  header_list=['#','TITLE','RATING']
  count = 0
  function_results = {}
  print("{: <3.3} {: <60.60} {: <6.6}".format(header_list[0],header_list[1],header_list[2]))
  for elem in results:
    count+=1
    function_results[count]=elem[0]
    print_count=str(count)
    print("{: <3.3} {: <60.60} {: <6.6}".format(print_count,elem[0],elem[1]))

  conn.commit()
  return function_results

###sort and print all books from group by the number of reviews###
def sort_number_reviews():
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()

  cur.execute('''SELECT Title,ReviewCount FROM Books WHERE ReviewCount NOT NULL ORDER BY ReviewCount DESC''')
  results = cur.fetchall()
  print(results)
  header_list=['#','TITLE','REVIEWS']
  count = 0
  function_results = {}
  print("{: <3.3} {: <60.60} {: <10.10}".format(header_list[0],header_list[1],header_list[2]))
  for elem in results:
    count+=1
    function_results[count] = elem[0]
    print_count=str(count)
    print("{: <3.3} {: <60.60} {: <10.10}".format(print_count,elem[0],str(elem[1])))

  conn.commit()
  return function_results

###before loading database, test if group books are already in databse###
###if group is not in database, delete previous data and load new group###
def db_test_else_load(group_id):

  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()


  books_insts = get_book_info(get_books_from_group(group_id))

  cur.execute('''SELECT GroupId FROM Books''')
  group_db = list(sum(cur.fetchall(), ()))

  if str(group_id) not in group_db:
    cur.execute('''DELETE FROM Books''')
    cur.execute('''DELETE FROM Settings''')
    conn.commit()

    try:
      load_db(books_insts)
      return books_insts
    except:
      return 'dbfailed'
  else:
    return 'dbloaded'

###when group is first searched in interactive program, print results (title of each book in group)###
def print_results():
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()

  cur.execute('''SELECT Title FROM Books''')
  results = list(sum(cur.fetchall(), ()))

  function_results = {}
  count = 0
  for elem in results:
    count+=1
    print_count=str(count)
    function_results[count] = elem
    print("{: <5.5} {: <20}".format(print_count,elem))

  conn.commit()
  return function_results

###when an active result set is loaded, user can enter amazon command and number of result to launch the amazon purchase page of that book###
def load_page(inp,function_results):
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()
  num_list = function_results.keys()
  if int(inp) in num_list:
    for k,v in function_results.items():
      num = k
      if num == inp:
        title = v
        statement = '''SELECT AmazonLink FROM Books WHERE Title = "'''+title+'''"'''
        cur.execute(statement)
        link = cur.fetchone()[0]
        print("Launching "+link+" in web browser")
        webbrowser.open(link, new=2, autoraise=True)
  else:
    print('Please enter a number in the active result set')


def interactive_program(command=None):
  print('Loading program...')
  conn = sqlite3.connect(DBNAME)
  cur = conn.cursor()

  options = "group <Goodreads Group ID>\n"+"\tavailable anytime\n"+"\tlists all books in a Goodreads Group\n"+"\tvalid inputs: valid Goodreads Group ID # \n\t(ex: 179584 for Our Shared Shelf or 85538 for Oprah's Book Club)\n"+"sort <kindle_price, average_rating, number_reviews>\n"+"\tavailable only if there is an active result set\n\tsorts list of books by given parameter\n\tvalid inputs: kindle_price, average_rating or number_reviews\namazon <result number>\n\tavailable only if there is an active result set\n\tlaunches a link to the Amazon page for the selected book\n\tvalid inputs: number of book in active result set\nmap\n\tavailable only if there is an active result set\n\tdisplays the setting (i.e. where the book takes place) of each book on a map\nreviews\n\tdisplays the popularity (number of reviews) for each book in a chart\nratings\n\tavailable only if there is an active result set\n\tdisplays the average rating for each book in a chart\nexit\n\texits the program\nhelp\n\tlists available commands"

  if command == None:
    command = input("Enter a command (or 'help' for options / 'exit' to quit): ")
  current = 0
  available_commands = ['help','exit','group','map','amazon','sort','ratings','reviews']
  function_results = None
  while command != 'exit':
      command_words = command.split()

      if command_words[0] not in available_commands:
          print("Please enter one of the available commands (enter 'help' for options / 'exit' to quit)")
          command = input("Enter a command (or 'help' for options / 'exit' to quit): ")

      command_words = command.split()
      if command == "help":
          print(options)
          command = input("1Enter a command (or 'help' for options / 'exit' to quit): ")

      command_words = command.split()
      if "group" in command:
        print('Loading data...')
        group = command_words[1]
        results = db_test_else_load(group)
        if results != "dbfailed":
          function_results = print_results()
          command = input("3Enter a command (or 'help' for options / 'exit' to quit): ")
        else:
          print('Invalid Group ID (or this group has no books). Try another group ID')
          command = input("2Enter a command (or 'help' for options / 'exit' to quit): ")

      command_words = command.split()
      if "sort" in command:
        sort_params = ["kindle_price","number_reviews","average_rating"]
        param = command_words[1]
        if param not in sort_params:
          print("Please enter a valid sort parameter: 'kindle_price', 'number_reviews', or 'average_rating'")
          command = input("Enter a command (or 'help' for options / 'exit' to quit): ")
        if param == "kindle_price":
          function_results = sort_kindle_price()
          command = input("Enter a command (or 'help' for options / 'exit' to quit): ")
        if param =="average_rating":
          function_results = sort_average_rating()
          command = input("Enter a command (or 'help' for options / 'exit' to quit): ")
        if param == "number_reviews":
          function_results = sort_number_reviews()
          command = input("Enter a command (or 'help' for options / 'exit' to quit): ")

      command_words = command.split()
      if "map" in command:
        plot_settings()
        command = input("7Enter a command (or 'help' for options / 'exit' to quit): ")

      command_words = command.split()
      if command_words[0]=="ratings":
        plot_ratings_dot()
        command = input("8Enter a command (or 'help' for options / 'exit' to quit): ")

      command_words = command.split()
      if 'reviews' in command:
        plot_review_count()
        command = input("9Enter a command (or 'help' for options / 'exit' to quit): ")

      command_words = command.split()
      if 'amazon' in command:
        if function_results != None:
          second_command = command.split()
          try:
            inp = int(second_command[1])
          except:
            inp = None
          if inp != None:
            load_page(inp,function_results)
            command = input("4Enter a command (or 'help' for options / 'exit' to quit): ")
          else:
            print("Please enter a number in the active result set")
            command = input("6Enter a command (or 'help' for options / 'exit' to quit): ")
        else:
          print("Please load an active result set first using group <group id>")
          command = input("6Enter a command (or 'help' for options / 'exit' to quit): ")
  return function_results


# interactive_program()
