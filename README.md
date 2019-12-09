# SI507_finalproj
Final Project Repo for SI507

This program is meant to display and visualize meta data for books read by any Goodreads Group. It is meant for readers looking for a quick way to see what the group has read (and therefore recommendations for reading material), and to analyze information like average ratings across books chosen. Users will also be able to follow Amazon purchase links if they want to buy a book that is listed. 

USER GUIDE:

The program accepts the following commands:

- group <Goodreads Group ID>
  - available anytime
  - lists all books in a Goodreads Group
  - valid inputs: valid Goodreads Group ID
  - (ex: 179584 for Our Shared Shelf or 85538 for Oprah's Book Club)
- sort <kindle_price, average_rating, number_reviews>
  - available only if there is an active result set (i.e. a group command has already been entered)
  - sorts list of books by given parameter
  - valid inputs: kindle_price, average_rating or number_reviews
- amazon <result number>
  - available only if there is an active result set
  - launches a link to the Amazon page for the selected book
  - valid inputs: number of book in active result set
- map
  - available only if there is an active result set
  - displays the setting (i.e. where the book takes place) of each book on a map
- reviews
  - available only if there is an active result set
  - displays the popularity (number of reviews) for each book in a chart
- ratings
  - available only if there is an active result set
  - displays the average rating for each book in a chart
- exit
  - exits the program
- help
  - lists available commands
  
*NOTE*: If running the finalproj_test.py file - this files is meant to test certain interactive functions within the program. At the end of certain tests, it will trigger the interative command. Enter "exit" each time it appears to move on to the next function and finish the test

DATA SOURCES USED:

- Scraped Goodreads pages including Group's bookshelf page that lists books the group has read, and book detail pages 
  - ex: Oprah's Book Club group bookshelf: https://www.goodreads.com/group/bookshelf/85538-oprah-s-book-club-official
  - Detail page for book: https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone
- Used Goodreads API (requires API Key) to get review and rating information for each book in group
  - API link: https://www.goodreads.com/api/index
- Used Google Places API to plot book "settings" (where each book takes place) 
  - API link: https://developers.google.com/places/web-service/search?authuser=2#PlaceSearchResults
- Used Plotly to generate data visualizations:
  - Plotly instructions: https://plot.ly/python/basic-charts/

See requirements.txt for list of required Python modules 

SIGNIFICANT FUNCTIONS:

- Book class:
  - creates Book instances using data scraped from Goodreads pages and using the Goodreads API. Book instance attributes are used to load data into database tables in the load_db function, lists of Book instances for the group are passed to functions below for additional processing 
- get_books_from_group & get_book_info:
  - scrapes data from the Goodreads Group bookshelf page(s) (get_books_from_group) and then scrapes individual book detail pages for book metadata (get_book_info). Get_book_info uses scraped data to create list of Book instances for all books in the Group 
- get_settings_dict & get_settings_place:
  - used with each other to call the Google Places API to get latitude and longitude info for settings locations (get_settings_place) and then create a comprehensive dictionary of all settings for all books in group (get_settings_dict)
- test_then_load_db:
  - tests to see if there is an existing database, then tests to see if group id user entered is already loaded in the          database. if it is not loaded, it loads the required data from listed data sources 
- plot_settings/review_count/ratings_dot:
  - calls the database to get relevant info, then plots settings/reviews/ratings in plotly 
- sort_kindle_price/number_reviews/average_rating:
  - calls the database to get relevant sorted info, then prints results sorted by given parameter
- load_page:
  - takes user number input and calls database to get appropriate amazon purchase page links for the selected book. then, launches that page in a browser  
- interactive_program:
  - processes user commands and calls appropriate function 

