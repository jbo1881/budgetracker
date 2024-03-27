import os
import mpld3
from flask import Flask, redirect, url_for, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import defer
from datetime import datetime
import calendar
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.ticker as ticker
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_required, login_user, current_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import email_validator
from flask import flash
from sqlalchemy.exc import IntegrityError

# Use Agg backend for Matplotlib
matplotlib.use('Agg')

app = Flask(__name__)


# SQLAlchemy configuration for the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
app.config['SECRET_KEY'] = 'BellAndSound97#'

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Flask-Login's login manager
login_manager = LoginManager()
login_manager.init_app(app)

# User Class
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    joined_at_date = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    transactions = db.relationship('Transactions', backref='user')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Registration Form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email address already exists. Please use a different email.')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different username.')

# Login form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

# Initialize Flask-Login's user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes for registration and login


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Email address is already registered. Please use a different email.', 'error')
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if True:
                login_user(user, remember=form.remember.data)
                # Fetch the user's transactions and pass them to the home template
                transactions = user.transactions
                return render_template("home.html", transactions=transactions)
            else:
                return redirect(url_for('login', _external=True, _scheme='https'))
    return render_template('login.html', form=form)

# Other routes and model definitions...
@app.route('/logout', methods=['GET','POST'])
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/users7676')
def users():
    users = User.query.all()
    return render_template('user.html', users=users)



class Transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(100), index=True, unique=False)
    month = db.Column(db.String(100), index=True, unique=False)
    amount = db.Column(db.Float, index=True, unique=False)
    category = db.Column(db.String(100), index=True, unique=False)
    income_expense = db.Column(db.String(100), index=True, unique=False)
    description = db.Column(db.String(100), index=True, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Corrected foreign key reference


# Home page
@app.route("/")
# @login_required
def home():
    if current_user.is_authenticated:
        # Query transactions only for the current user
        transactions = Transactions.query.filter_by(user_id=current_user.id).order_by(Transactions.date).all()
    else:
        # If not logged in, display no transactions
        transactions = []


    month_name = calendar.month_name[datetime.now().month]
    return render_template("home.html", transactions=transactions, month_name=month_name)

# Function to convert format string to Python datetime object


def convert_to_datetime(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

# Function to retrieve the name of the month from the date


def get_month_name(date):
    month_name = date.strftime("%B")  # %B gives the full month name
    return month_name

# Create transaction page


@app.route("/create-transaction", methods=['POST'])
def create():
    if current_user.is_authenticated:
        try:
            date = convert_to_datetime(request.form['date'])
            category = request.form['category']
            income_expense = 'Income' if category in ['Salary', 'Side hustle', 'Investments'] else 'Expense'
    
            transaction = Transactions(
                date=date,
                month=get_month_name(date),
                amount=float(request.form['amount']),
                category=category,
                income_expense=income_expense,
                description=request.form['description'],
                user_id=current_user.id
            )
    
            db.session.add(transaction)
            db.session.commit()
            return redirect(url_for("home"))
        except Exception as e:
            # Handle exceptions
            return redirect(url_for("home"))
    else:
        # Handle the case where the user is not logged in
        return redirect(url_for("login"))




# Delete transaction
@app.route("/delete/<id>")
def deleteTransaction(id):
    trans = Transactions.query.filter_by(id=int(id)).delete()
    db.session.commit()
    return redirect(url_for("home"))

#Delete ALL
@app.route("/delete_all", methods=["POST"])
def delete_all_transactions():
    # Delete all transactions in your database
    Transactions.query.delete()
    db.session.commit()
    return redirect(url_for("home"))


# EDIT transaction page
@app.route("/edit/<int:id>", methods=['GET', 'POST'])
def edit(id):
    trans = Transactions.query.get_or_404(id)

    if request.method == 'POST':
        date = convert_to_datetime(request.form['date'])
        category = request.form['category']
        income_expense = 'Income' if category in [
            'Salary', 'Side hustle', 'Investments'] else 'Expense'

        # Update the existing transaction instead of creating a new one
        trans.date = date
        trans.month = get_month_name(date)
        trans.amount = request.form['amount']
        trans.category = category
        trans.income_expense = income_expense
        trans.description = request.form['description']

        db.session.commit()
        return redirect(url_for("home"))

    return render_template('edit.html', trans=trans)


# Personal Finance Dashboard
@app.route("/personal-finance-dashboard")
def dashboard():
    transactions = Transactions.query.filter_by(user_id=current_user.id).filter(
    Transactions.date >= datetime(2024, 1, 1),
    Transactions.date < datetime(2025, 1, 1)
).all()


    # Function total
    def total_monthly(monthly_totals):
        total_amount = sum(monthly_totals.values())
        return total_amount

    # Function average
    def average_monthly(total_amount, monthly_totals):
        months_0 = 0
        for months0 in monthly_totals.keys():
            if monthly_totals[months0] != 0:
                months_0 += 1
        try:
            average = round(total_amount / months_0, 2)
        except ZeroDivisionError:
            average = 0
        return average

    monthly_income_totals = {
        'January': 0,
        'February': 0,
        'March': 0,
        'April': 0,
        'May': 0,
        'June': 0,
        'July': 0,
        'August': 0,
        'September': 0,
        'October': 0,
        'November': 0,
        'December': 0
    }

    for trans in transactions:
        if trans.income_expense == 'Income':
            monthly_income_totals[trans.month] += trans.amount

    # Calculate total and average incomes
    # Total income
    total_income = total_monthly(monthly_income_totals)
    # Average income
    average_income = average_monthly(total_income, monthly_income_totals)

    monthly_expense_totals = {
        'January': 0,
        'February': 0,
        'March': 0,
        'April': 0,
        'May': 0,
        'June': 0,
        'July': 0,
        'August': 0,
        'September': 0,
        'October': 0,
        'November': 0,
        'December': 0
    }

    for trans in transactions:
        if trans.income_expense == 'Expense':
            monthly_expense_totals[trans.month] += trans.amount

    # Calculate total and average expenses
    total_expense = total_monthly(monthly_expense_totals)
    average_expense = average_monthly(total_expense, monthly_expense_totals)

    # Savings
    monthly_savings_totals = {
        'January': 0,
        'February': 0,
        'March': 0,
        'April': 0,
        'May': 0,
        'June': 0,
        'July': 0,
        'August': 0,
        'September': 0,
        'October': 0,
        'November': 0,
        'December': 0
    }

    for trans in transactions:
        if trans.income_expense == 'Expense':
            monthly_savings_totals[trans.month] += -trans.amount
        else:
            monthly_savings_totals[trans.month] += trans.amount

    # Calculate total and average savings
    total_savings = total_monthly(monthly_savings_totals)
    average_savings = average_monthly(total_savings, monthly_savings_totals)

    # Obtain current month
    current_month = datetime.now().month

    # Generate Income-Expense Plot dynamically


    def income_expense_plot(transactions):
        # Plotting
        plt.figure(figsize=(5.5, 4))
        months = list(monthly_expense_totals.keys())
        amounts = list(monthly_expense_totals.values())

        plt.bar(months, amounts, color='#ce0606', label='Expense')

        # Annotate each bar with its value
        for i, value in enumerate(amounts):
            plt.text(i, value + 0.1, f'{int(value)}€', ha='center', va='baseline', fontname='Verdana', fontsize=8, color='r')

        plt.xlabel('Month', fontdict={'fontname': 'Verdana', 'fontsize': 12})
        plt.ylabel('Amount (€)', fontdict={'fontname': 'Verdana', 'fontsize': 12})
        plt.title('Income & Expense Comparison', fontdict={'fontname': 'Verdana', 'fontsize': 16, 'fontweight': 'bold'})
        

        # Plot Income
        income = list(monthly_income_totals.values())
        plt.plot(months, income, color='#009901', marker='+', mfc='white', markersize=3, label='Income')

        for i, value in enumerate(income):
            plt.text(i, value, f'{int(value)}€', ha='center', va='bottom', fontname='Verdana', fontsize=8, color='g')


        # Add legend with custom font
        plt.legend(prop={'family': 'Verdana'})

        plt.grid(axis = 'y', linestyle = '-', linewidth = 0.1, alpha=0.05)
        
        # Convert month names to datetime objects
        month_objects = [datetime.strptime(month, "%B") for month in months]

        # Get short month names
        short_month_names = [obj.strftime("%b") for obj in month_objects]

        # Set x-axis tick labels to be the names of the months
        plt.gca().set_xticklabels(short_month_names, fontname='Verdana', fontsize=10)        

        # Convert Matplotlib plot to HTML using mpld3
        plot_html = mpld3.fig_to_html(plt.gcf())

        plt.close(plt.gcf())

        return plot_html


    # Get the matplotlib plot
    plot_html = income_expense_plot(transactions)

    #CATEGORIES
    def sum_category(cat):
        return sum(transaction.amount for transaction in 
               Transactions.query.options(defer(Transactions.user_id)).filter(Transactions.category == cat).all())

    #INCOME
    #Salary
    sum_salary = sum_category('Salary')
    #Side hustle
    sum_sidehustle = sum_category('Side hustle')
    #Investments
    sum_investments = sum_category('Investments')

    #EXPENSE
    #Housing
    sum_housing = sum_category('Housing')
    #Transportation
    sum_transportation = sum_category('Transportation')
    #Food
    sum_food = sum_category('Food')
    #Utilities
    sum_utilities = sum_category('Utilities')
    #Medical
    sum_medical = sum_category('Medical')
    #Leisure
    sum_leisure = sum_category('Leisure')
    #Education
    sum_education = sum_category('Education')


    def categories_plot():
        # Define data
        data = [sum_salary, sum_sidehustle, sum_investments, sum_housing, sum_transportation,
            sum_food, sum_utilities, sum_medical, sum_leisure, sum_education]
        categories = ['Salary', 'Side hustle', 'Investments', 'Housing', 'Transportation',
                    'Food', 'Utilities', 'Medical', 'Leisure', 'Education']
        # Define colors
        green_palette = ['#008000', '#32CD32', '#00FF00']  # Green palette for the first 3 categories
        red_palette = ['#FF6347', '#DC143C', '#B22222', '#8B0000', '#FF0000']  # Red palette for the rest
        
        # Assign colors based on category
        colors = []
        for i, category in enumerate(categories):
            if i < 3:  # First 3 categories
                colors.append(green_palette[i])
            else:  # Rest of the categories
                colors.append(red_palette[i % len(red_palette)])  # Ensure looping through the red palette
    
        # Creating plot
        plt.figure(figsize=(6.5, 4))
        plt.barh(categories, data, color=colors)
        plt.title('Category Breakdown', fontdict={'fontname': 'Verdana', 'fontsize': 16, 'fontweight': 'bold'})
        plt.xlabel('Amount (€)', fontdict={'fontname': 'Verdana', 'fontsize': 12})
        plt.ylabel('Categories', fontdict={'fontname': 'Verdana', 'fontsize': 12})
        
        # Adding values on bars
        for i, value in enumerate(data):
            plt.text(value, i, f'{int(value)}€', va='center', fontsize=8)
        
        # Adding legend
        #plt.legend(categories, loc="best", fontsize='small', title='Categories', title_fontsize='medium')
        plt.grid(axis = 'x', linestyle = '-', linewidth = 0.1, alpha=0.05)


        # Set x-axis tick labels to be the names of the months
        plt.gca().set_yticklabels(categories, fontname='Verdana', fontsize=10)  
        
        # Convert Matplotlib plot to HTML using mpld3
        plot_html_bar = mpld3.fig_to_html(plt.gcf())
        
        plt.close(plt.gcf())

        return plot_html_bar

        # Get the matplotlib plot
    plot_html_bar = categories_plot()


    return render_template("dashboard.html", monthly_income_totals=monthly_income_totals, total_income=total_income, average_income=average_income,
                           monthly_expense_totals=monthly_expense_totals, total_expense=total_expense, average_expense=average_expense,
                           monthly_savings_totals=monthly_savings_totals, total_savings=total_savings, average_savings=average_savings,
                           current_month=current_month, plot_html=plot_html, sum_salary=sum_salary, sum_sidehustle=sum_sidehustle,
                           sum_investments=sum_investments, sum_housing=sum_housing, sum_transportation=sum_transportation, sum_food=sum_food,
                           sum_utilities=sum_utilities, sum_medical=sum_medical, sum_leisure=sum_leisure, sum_education=sum_education,
                           plot_html_bar=plot_html_bar)

# TEMPLATES



# from sqlalchemy import text

# # Function to reset transactions table
# def reset_transactions_table():
#     with app.app_context():
#         # Get a database connection
#         conn = db.engine.connect()
        
#         # Drop existing transactions table if it exists
#         drop_statement = text('DROP TABLE IF EXISTS transactions')
#         conn.execute(drop_statement)
        
#         # Recreate transactions table with the desired schema
#         db.create_all()

#         # Close the connection
#         conn.close()

# # Call the function to reset transactions table
# reset_transactions_table()



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
