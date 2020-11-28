from decimal import Decimal
import requests
import main_functions
from bson import Decimal128
from flask import Flask, render_template, request, url_for
from flask_pymongo import PyMongo, MongoClient
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, DateField

app = Flask(__name__)
app.config["SECRET_KEY"] = "IKLtJCaKASKwKNLw"
app.config["MONGO_URI"] = "mongodb+srv://cop4813:IKLtJCaKASKwKNLw@learningMongoDB.d9vny.mongodb.net/project3?retryWrites=true&w=majority"
mongo = PyMongo(app)

class Expenses(FlaskForm):
    list_URL = "http://api.currencylayer.com/list?access_key=7edb40d73b258f5cf730f823f226aa7e"
    response = requests.get(list_URL).json()

    # retrieve the list of names and save it in a json file
    currency_list_names_file_name = "JSON_Files\\currency_list_names.json"
    main_functions.save_to_file(response, currency_list_names_file_name)

    # read the json file and extract all the names in an array of tuples
    currency_names = main_functions.read_from_file(currency_list_names_file_name)
    name_list = []
    for x in currency_names["currencies"]:  # range(len(currency_names['currencies'])):
        name_list.append((x, currency_names['currencies'][x]))

    # instantiate the required input fields and add the current parameters for the genre options
    currency = SelectField(choices=[(x, y) for x, y in name_list])
    categories = ['Food & Drinks', 'Health', 'Travel', 'Entertainment', 'Shopping', 'Services']
    description = StringField('Description')
    category = SelectField('Categories', choices=categories)
    cost = DecimalField('Cost ($)')
    date = DateField('Date', format='%m/%d/%Y')
    # TO BE COMPLETED (please delete the word pass above)

def get_total_expenses(category):
    expense_list = mongo.db.expenses.find()
    expense_of_category = Decimal(0.0)
    for i in expense_list:
        if i['category'] == category:
            expense_of_category += i['cost'].to_decimal()
    return expense_of_category
    # TO BE COMPLETED (please delete the word pass above)


@app.route('/')
def index():
    my_expenses = mongo.db.expenses.find()
    total_cost=0
    for i in my_expenses:
        total_cost+=float(i["cost"].to_decimal())
    expensesByCategory = []
    for category in Expenses.categories:
        expensesByCategory.append((category, get_total_expenses(category)))

    # expensesByCategory is a list of tuples
    # each tuple has two elements:
    ## a string containing the category label, for example, insurance
    ## the total cost of this category
    return render_template("index.html", expenses=total_cost, expensesByCategory=expensesByCategory)


@app.route('/addExpenses', methods=["GET", "POST"])
def addExpenses():
    # INCLUDE THE FORM
    expensesForm = Expenses()
    if request.method == "POST":
        # INSERT ONE DOCUMENT TO THE DATABASE
        # CONTAINING THE DATA LOGGED BY THE USER
        # REMEMBER THAT IT SHOULD BE A PYTHON DICTIONARY
        input_description = expensesForm.description.data
        input_category = expensesForm.category.data
        input_cost = expensesForm.cost.data
        input_date = expensesForm.date.data
        input_currency = expensesForm.currency.data

        final_cost = currency_converter(input_cost, input_currency)

        if input_cost:
            expense = {'description': input_description, 'category': input_category, 'cost': Decimal128(Decimal(str(final_cost))), 'date': str(input_date)}

            mongo.db.expenses.insert_one(expense)

            return render_template("expenseAdded.html")
    return render_template("addExpenses.html", form=expensesForm)


def currency_converter(cost, currency):
    url="http://api.currencylayer.com/live?access_key=7edb40d73b258f5cf730f823f226aa7e"
    response = requests.get(url).json()

    # create the key for the exchange rate
    conversion_to_find = "USD" + currency

    # save the response to a json file
    response_file_name = "JSON_Files\\currency_list_rates.json"
    main_functions.save_to_file(response, response_file_name)

    # read the json file and extract all the names in an array of tuples
    currency_rates = main_functions.read_from_file(response_file_name)

    # extract the relevant exchange rate
    rate = currency_rates['quotes'][conversion_to_find]

    # exchange formula
    converted_cost = cost/Decimal(str(rate))

    return converted_cost

app.run()