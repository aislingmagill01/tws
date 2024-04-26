from flask import Flask, request, jsonify, render_template, url_for, redirect, flash, send_from_directory, session
from pymongo import MongoClient
from flask_login import UserMixin
from bson import ObjectId
import json
import os

# copied from B4 for client log in pg4 

app = Flask(__name__)
app.secret_key = 'mysecret' # setting secret key

# JWT Setup


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

INVOICE_FOLDER = 'invoices'
app.config['INVOICE_FOLDER'] = INVOICE_FOLDER

# connect to MongoDB client 
client = MongoClient ("mongodb://localhost:27017")
db = client['my_database']

client_details_collection = db['client_details']
bookings_collection = db['bookings']
upload_file_collection = db['upload_file']
invoice_client_collection = db['invoice_client']
client_reviews_collection = db['client_reviews']
services_collection = db["services"]

  # Read the JSON file
with open('C:\\Users\\B00805449\OneDrive - Ulster University\\Documents\\Final Year\\COM668 Computing Project\\practice_1\\my_database.json', 'r') as file:
        data = json.load(file)


client_details_collection.insert_many(data['client_details']) 
bookings_collection.insert_many(data['bookings']) 
upload_file_collection.insert_many(data['upload_file']) 
invoice_client_collection.insert_many(data['invoice_client']) 
client_reviews_collection.insert_many(data['client_reviews']) 
services_collection.insert_many(data['services'])

# Create Homepage route
@app.route('/')
def index():
    return render_template('index.html')


# Create a User login 
class User(UserMixin):
    def __init__(self, client_user_id, username, password):
        self.id = client_user_id
        self.username = username
        self.password = password

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return jsonify({'error': 'Username or password missing'}), 400

        # Query the collection for the user with the provided username and password
        user = client_details_collection.find_one({'username': username, 'password': password})
        if user:
            session['username'] = username
            return redirect('/')
        else:
            return "Invalid username or password", 401  # Unauthorized status code

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return "Username or password missing. Please fill out both fields."

        # Check if username already exists
        existing_user = client_details_collection.find_one({'username': username})
        if existing_user:
            return "Username already exists. Please choose another one."
        
        # If username is unique, create a new user
        new_user = {
            "client_user_id": str(client_details_collection.count_documents({}) + 1).zfill(3),
            "username": username,
            "password": password,
            # Add other user details as required
        }
        client_details_collection.insert_one(new_user)
        
        # Redirect to login page or any other page
        return redirect('/login')  # Redirect to the login page

    return render_template('register.html')


# Logout route using POST request 
@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Redirect the user to the login page
    return redirect(url_for('index'))


@app.route('/type/family')
def family_detail():
    # Render detail page for Family type
    return render_template('family_detail.html')

@app.route('/type/criminal')
def criminal_detail():
    # Render detail page for Criminal type
    return render_template('criminal_detail.html')

@app.route('/type/legal')
def legal_detail():
    # Render detail page for Legal type
    return render_template('legal_detail.html')


# Services avilable page
# Render template to show list of services
@app.route('/services')
def services():
    return render_template('services.html ')

@app.route('/service/<service_name>')
def service_information(service_name):
    services = list(services_collection.find({'Service': service_name}))
    print("Services avilable for", service_name, ":", services)

    review = list(client_reviews_collection.find({'service_name': {'$in': [r['id']for r in services]}}))
    return render_template('services.html', services=service_name)

    

# Booking Page 
# Create a portal for clients to book appaointments 



# Create a route to  book appointments 
@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if request.method == 'POST':
        Full_name = request.form.get('name')
        email = request.form.get('email')
        client_user_id = request.form.get('client_user_id')
        service_name = request.form.get('service_name')
        date = request.form.get('date')
        
        # Validate input (e.g., check if fields are not empty)
        if Full_name and email and date:
            # Save booking to MongoDB
            booking = {
                'Full Name': Full_name,
                'email': email,
                'client_user_id': client_user_id, 
                'Date': date,
                'Service Required': service_name
            }
            bookings_collection.insert_one(booking)
            flash('Booking successful!', 'success')
            return redirect(url_for('book_appointment'))
        else:
            flash('Please fill in all fields', 'error')

    return render_template('book_appointment.html')


# view appointments 
@app.route('/view_booking/<booking_id>')
def view_booking(booking_id):
    # Retrieve the booking details from the database using the provided booking_id
    booking = bookings_collection.find_one({'_id': ObjectId(booking_id)})
    
    if booking:
        # Render a template with the booking details
        return render_template('view_booking.html', booking=booking)
    else:
        # Handle the case where the booking with the provided ID does not exist
        return 'Booking not found', 404
    
    

# cancel appointments 
@app.route('/cancel_booking/<booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    # Check if the booking exists
    booking = bookings_collection.find_one({'_id': ObjectId(booking_id)})
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

# Delete the booking
    result = bookings_collection.delete_one({'_id': ObjectId(booking_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Failed to cancel booking"}), 500

    return jsonify({"message": "Booking cancelled successfully"}), 200



# Create area for clients and staff to upload/ view/ delete documents 

# Route to upload a file

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if 'file' not in request.files:
            return render_template('upload.html', data='No file part')
        
        uploaded_file = request.files['file']
        
        if uploaded_file.filename == '':
            return render_template('upload.html', data='No selected file')
        
        destination = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(destination)
        
        return render_template('upload.html', data='File Uploaded Successfully')
    
    return render_template('upload.html')
   
# Route to view a file
@app.route("/view/<filename>", methods=["GET"])
def view_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return render_template('view_file.html', file_found=True, filename=filename)
    else:
        return render_template('view_file.html', file_found=False, error_message="File not found")

@app.route("/uploaded_files")
def list_uploaded_files():
    # Here you can list all uploaded files or render a page showing uploaded files
    # For now, let's just render a simple template
    return render_template('uploaded_files.html')


# Route to delete a file
@app.route("/delete/<filename>", methods=["DELETE"])
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return redirect(url_for('upload'))  # Redirect to the upload route or any other route after successful deletion
    else:
        return "File not found"

@app.route("/delete_files")
def delete_files():
    # Here you can list all uploaded files or render a page showing uploaded files
    # For now, let's just render a simple template
    return render_template('delete_files.html')

# Route to upload a file

# Create route to uplaod invocies 


@app.route("/invoicing", methods=["GET", "POST"])
def invoicing():
    if request.method == "POST":
        if 'file' not in request.files:
            return render_template('invoicing.html', data='No file part')
        
        invoice_file = request.files['file']
        
        if invoice_file.filename == '':
            return render_template('invoicing.html', data='No selected file')
        
        destination = os.path.join(app.config['INVOICES_FOLDER'], invoice_file.filename)
        invoice_file.save(destination)
        
        return render_template('invoicing.html', data='Invoice Uploaded Successfully')
    
    return render_template('invoicing.html')
   
# Route to view a invoice
@app.route("/invoices/<filename>")
def uploaded_invoice(filename):
    return send_from_directory(app.config['INVOICE_FOLDER'], filename)

@app.route("/uploaded_invoice_list")
def uploaded_invoice_list():
    # Here you can list all uploaded files or render a page showing uploaded files
    # For now, let's just render a simple template
    return render_template('uploaded_invocie_list.html')





# Create route to uplaod invocies 



# Update the client with case information 




# Client reviews
@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
 if request.method == 'POST':
    reviewer_name = request.form.get('reviewer_name')
    feedback = request.form.get('feedback')

    feedback_data = {
        "name": reviewer_name,
        "feedback": feedback
        }
    
    client_reviews_collection.insert_one(feedback_data)
    flash('Review submitted successfully!', 'success')
    return redirect(url_for('add_review'))
    

 return render_template('add_review.html')
    

if __name__ == "__main__":
    app.run(debug=True)


