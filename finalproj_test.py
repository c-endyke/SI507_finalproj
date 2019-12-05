import unittest
from finalproj import *

db_test_else_load(85538)

class TestDatabase(unittest.TestCase):

    def test_book_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = 'SELECT Title FROM Books'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Love Warrior',), result_list)
        self.assertEqual(len(result_list), 130)

        sql = '''
            SELECT Title, AverageRating, KindlePrice
            FROM Books
            WHERE KindlePrice NOT NULL
            ORDER BY AverageRating DESC
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        #print(result_list)
        self.assertEqual(result_list[0][1], 4.42)
        self.assertEqual(result_list[0][2],  11.65)
        self.assertEqual(len(result_list),71)

        conn.close()

    def test_setting_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT Location
            FROM Settings
            WHERE Book=10
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Kenya',), result_list)
        self.assertEqual(len(result_list), 6)

        sql = '''
            SELECT COUNT(*)
            FROM Settings
        '''
        results = cur.execute(sql)
        count = results.fetchone()[0]
        self.assertTrue(count == 77)

        conn.close()

    def test_joins(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT Settings.Location
            FROM Settings
            JOIN Books ON Settings.Book = Books.Id
            WHERE Books.Title = "The Underground Railroad"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Indiana',), result_list)
        self.assertEqual(len(result_list),5)
        conn.close()

class TestSort(unittest.TestCase):

    def test_price_sort(self):
        results = sort_kindle_price()
        first_title = results[1]
        self.assertEqual(first_title, 'The Purpose Driven Life: What on Earth Am I Here for?')
        self.assertEqual(len(results.items()),71)

    def test_rating_sort(self):
        results = sort_average_rating()
        first_title = results[1]
        self.assertEqual(first_title, 'The Treasure Hunt: A Little Bill Book')
        self.assertEqual(len(results.items()),118)

    def test_review_sort(self):
        results = sort_number_reviews()
        first_title = results[1]
        self.assertEqual(first_title, 'Eat, Pray, Love')
        self.assertEqual(len(results.items()),118)

class TestInteractiveProgram(unittest.TestCase):

    def test_interactive_program(self):
         group_results = interactive_program("group 85538")
         self.assertEqual(len(group_results.items()),130)

         ###User must enter 'exit' in command after each interactive program call#######

         sort_price_results = interactive_program("sort kindle_price")
         self.assertEqual(len(sort_price_results.items()),71)

         ###User must enter 'exit' in command after each interactive program call#######

         sort_rating_results = interactive_program("sort average_rating")
         self.assertEqual(len(sort_rating_results.items()),118)

        ###User must enter 'exit' in command after each interactive program call#######

         sort_review_results = interactive_program("sort number_reviews")
         self.assertEqual(len(sort_review_results.items()),118)


class TestPlotly(unittest.TestCase):

    def test_map(self):
        try:
            plot_settings()
        except:
            self.fail()

    def test_plot_ratings(self):
        try:
            plot_ratings_dot()
        except:
            self.fail()

    def test_plot_reviews(self):
        try:
            plot_review_count()
        except:
            self.fail()


unittest.main()
