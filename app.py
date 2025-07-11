# Import necessary libraries
from flask import Flask, render_template, request, jsonify  # Flask web framework components
import joblib  # For loading the trained machine learning model
import numpy as np  # For numerical operations
import pandas as pd 
import io  # For handling CSV data in memory
# For database connection and operations
import psycopg2# For data manipulation (if needed)
from psycopg2.extras import RealDictCursor  # For returning query results as dictionaries

import os
from dotenv import load_dotenv
# Initialize Flask application
app = Flask(__name__)

# ==============================================
# DATABASE CONFIGURATION
# ==============================================
load_dotenv()
# Configure PostgreSQL connection settings

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        cursor_factory=RealDictCursor
    )
import os
import psycopg2

from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    Customer_ID SERIAL PRIMARY KEY,
    Age INT,
    Gender INT,
    District INT,
    Region INT,
    Location_Type INT,
    Customer_Type INT,
    Employment_Status INT,
    Income_Level FLOAT,
    Education_Level INT,
    Tenure INT,
    Balance FLOAT,
    Credit_Score INT,
    Outstanding_Loans FLOAT,
    Num_Of_Products INT,
    Mobile_Banking_Usage INT,
    Number_of_Transactions_per_Month INT,
    Num_Of_Complaints INT,
    Proximity_to_NearestBranch_or_ATM_km FLOAT,
    Mobile_Network_Quality INT,
    Owns_Mobile_Phone INT,
    prediction INT,
    Churn_Probability FLOAT
);
""")


conn.commit()
cursor.close()
conn.close()




# ==============================================
# MODEL LOADING
# ==============================================

# Load the pre-trained LightGBM model from file
model = joblib.load('lgb_model.pkl')
# ==============================================
# ROUTE DEFINITIONS
# ==============================================

@app.route('/customers')
def customers_page():
    return render_template("customers.html")

# Home page route - redirects to login
@app.route('/')
def home():
    """Render the login page as the home page"""
    return render_template('index.html')

# About page route
@app.route('/about')
def about():
    """Render the about page"""
    return render_template('about.html')
# Contacts page route
@app.route('/contacts')
def contacts():
    """Render the contacts page"""
    return render_template('contacts.html')

# Login page route
@app.route('/index')
def login():
    """Render the login page"""
    return render_template('index.html')

# Main dashboard/churn analysis page
@app.route('/churn')
def dashboard():
    """
    Render the churn analysis dashboard with customer data
    and total customer count
    """
    try:
        # Create a database cursor
        conn = get_db_connection()
        cursor = conn.cursor()

        
        # Execute query to get customer data
        cursor.execute("SELECT * FROM customers LIMIT 10")  # Sample customers
        customers = cursor.fetchall()
        
        # Execute query to get total customer count
        cursor.execute("SELECT COUNT(*) as total_customers FROM customers")
        count_result = cursor.fetchone()
        total_customers = count_result['total_customers']
        
        # Close the cursor
        cursor.close()
        
        # Render template with both customer data and total count
        return render_template('churn.html', 
                            customers=customers,
                            total_customers=total_customers)
    
    except Exception as e:
        print("Database error:", str(e))
        return render_template('churn.html', 
                            customers=[], 
                            total_customers=0,
                            error=str(e))
# Prediction API endpoint
@app.route('/predict', methods=['POST'])
def predict():
    """
    Handles prediction, saves input + prediction into DB, and returns feedback.
    """
    try:
        data = request.get_json()

        # Feature order must match training
        features = np.array([
            int(data['Age']),
            int(data['Gender']),
            int(data['District']),
            int(data['Region']),
            int(data['Location_Type']),
            int(data['Customer_Type']),
            int(data['Employment_Status']),
            float(data['Income_Level']),
            int(data['Education_Level']),
            int(data['Tenure']),
            float(data['Balance']),
            int(data['Credit_Score']),
            float(data['Outstanding_Loans']),
            int(data['Num_Of_Products']),
            int(data['Mobile_Banking_Usage']),
            int(data['Number_of_Transactions_per_Month']),
            int(data['Num_Of_Complaints']),
            float(data['Proximity_to_NearestBranch_or_ATM_km']),
            int(data['Mobile_Network_Quality']),
            int(data['Owns_Mobile_Phone'])
        ]).reshape(1, -1)

        # Predict
        probabilities = model.predict_proba(features)
        prob_churn = float(probabilities[0][1])
        prediction = 1 if prob_churn >= 0.5 else 0
        prob_percentage = round(prob_churn * 100, 2)

        # Insert into DB
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO customers (
                Age, Gender, District, Region, Location_Type, Customer_Type,
                Employment_Status, Income_Level, Education_Level, Tenure,
                Balance, Credit_Score, Outstanding_Loans, Num_Of_Products,
                Mobile_Banking_Usage, Number_of_Transactions_per_Month,
                Num_Of_Complaints, Proximity_to_NearestBranch_or_ATM_km,
                Mobile_Network_Quality, Owns_Mobile_Phone,
                prediction, Churn_Probability
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            data['Age'], data['Gender'], data['District'], data['Region'], data['Location_Type'],
            data['Customer_Type'], data['Employment_Status'], data['Income_Level'],
            data['Education_Level'], data['Tenure'], data['Balance'], data['Credit_Score'],
            data['Outstanding_Loans'], data['Num_Of_Products'], data['Mobile_Banking_Usage'],
            data['Number_of_Transactions_per_Month'], data['Num_Of_Complaints'],
            data['Proximity_to_NearestBranch_or_ATM_km'], data['Mobile_Network_Quality'],
            data['Owns_Mobile_Phone'], prediction, prob_churn
        ))

        conn.commit()
        cursor.close()
        conn.close()

        # Send success feedback
        return jsonify({
            "message": "Customer added and prediction saved successfully.",
            "prediction": "Customer will leave" if prediction == 1 else "Customer will stay",
            "probability": prob_percentage,
            "success": True
        })

    except Exception as e:
        print("Prediction error:", str(e))
        return jsonify({
            "error": f"Prediction failed: {str(e)}",
            "success": False
        }), 500

# Add this new endpoint to handle batch predictions
@app.route('/api/customers/predict_all', methods=['POST'])
def predict_all_customers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()


        # Fetch customers needing predictions
        cursor.execute("""
            SELECT * FROM customers 
            WHERE prediction IS NULL
            LIMIT 10000
        """)
        customers = cursor.fetchall()

        if not customers:
            cursor.close()
            return jsonify({
                'success': True,
                'processed': 0,
                'message': "No customers left to process."
            })

        # List of features in the order expected by the model
        model_features = getattr(model, 'feature_name_', [
            'Age', 'Gender', 'District', 'Region', 'Location_Type', 
            'Customer_Type', 'Employment_Status', 'Income_Level',
            'Education_Level', 'Tenure', 'Balance', 'Credit_Score',
            'Outstanding_Loans', 'Num_Of_Products', 'Mobile_Banking_Usage',
            'Number_of_Transactions_per_Month', 'Num_Of_Complaints',
            'Proximity_to_NearestBranch_or_ATM_km', 'Mobile_Network_Quality',
            'Owns_Mobile_Phone'
        ])

        # Mappings from your data
        region_map = { "Southern": 0, "Northern": 1, "Central": 2 }
        gender_map = { "Male": 1, "Female": 0 }
        district_map = {
            "Dedza": 6, "Dowa": 26, "Kasungu": 10, "Lilongwe": 22, "Mchinji": 8,
            "Nkhotakota": 12, "Ntcheu": 27, "Ntchisi": 9, "Salima": 21, "Chitipa": 11,
            "Karonga": 5, "Likoma": 20, "Mzimba": 16, "Nkhata Bay": 3, "Rumphi": 24,
            "Balaka": 25, "Blantyre": 17, "Chikwawa": 2, "Chiradzulu": 7,
            "Machinga": 4, "Mangochi": 14, "Mulanje": 15, "Mwanza": 23,
            "Nsanje": 18, "Thyolo": 1, "Phalombe": 19, "Zomba": 0, "Neno": 13
        }
        customertype_map = { "Retail": 0, "SME": 1, "Corporate": 2 }
        employmentstatus_map = { "Self Employed": 0, "Not Employed": 1, "Employed": 2 }
        educationlevel_map = { "Primary": 0, "Secondary": 1, "Tertiary": 2 }
        netquality_map = { "Fair": 0, "Poor": 1, "Good": 2 }
        phone_map = { "Yes": 0, "No": 1 }
        mobilebank_map = { "No": 0, "Yes": 1 }
        locationtype_map = { "Rural": 0, "Urban": 1, "Semi Urban": 2 }

        processed_count = 0

        def safe_int(val):
            return int(val) if val not in (None, '', 'NULL') else 0

        def safe_float(val):
            return float(val) if val not in (None, '', 'NULL') else 0.0

        for customer in customers:
            try:
                feature_values = {
                    'Age': safe_int(customer.get('Age')),
                    'Gender': gender_map.get(customer.get('Gender'), 0),
                    'District': district_map.get(customer.get('District'), 0),
                    'Region': region_map.get(customer.get('Region'), 0),
                    'Location_Type': locationtype_map.get(customer.get('Location_Type'), 0),
                    'Customer_Type': customertype_map.get(customer.get('Customer_Type'), 0),
                    'Employment_Status': employmentstatus_map.get(customer.get('Employment_Status'), 0),
                    'Income_Level': safe_float(customer.get('Income_Level')),
                    'Education_Level': educationlevel_map.get(customer.get('Education_Level'), 0),
                    'Tenure': safe_int(customer.get('Tenure')),
                    'Balance': safe_float(customer.get('Balance')),
                    'Credit__Score': safe_int(customer.get('Credit_Score')),
                    'Outstanding_Loans': safe_float(customer.get('Outstanding_Loans')),
                    'Num_Of_Products': safe_int(customer.get('Num_Of_Products')),
                    'Mobile_Banking_Usage': mobilebank_map.get(customer.get('Mobile_Banking_Usage'), 0),
                    'Number_of__Transactions_per/Month': safe_int(customer.get('Number_of_Transactions_per_Month')),
                    'Num_Of_Complaints': safe_int(customer.get('Num_Of_Complaints')),
                    'Proximity_to_NearestBranch_or_ATM_(km)': safe_float(customer.get('Proximity_to_NearestBranch_or_ATM_km')),
                    'Mobile_Network_Quality': netquality_map.get(customer.get('Mobile_Network_Quality'), 0),
                    'Owns_Mobile_Phone': phone_map.get(customer.get('Owns_Mobile_Phone'), 0)
                }

                features = np.array([feature_values[col] for col in model_features]).reshape(1, -1)

                prob_churn = model.predict_proba(features)[0][1]
                
                prediction = int(prob_churn >= 0.5)
                
                customer_id = safe_int(customer.get('Customer_ID'))
                
                cursor.execute("""
                    UPDATE customers 
                    SET prediction = %s,
                        Churn_Probability = %s
                    WHERE Customer_ID = %s
                """, (prediction, float(prob_churn), customer_id))

                if cursor.rowcount == 0:
                    print(f"No rows updated for Customer_ID {customer_id}. Check if ID exists.")
                else:
                    print(f"Updated Customer_ID {customer_id}")
                    processed_count += 1

            except Exception as e:
                print(f"Error processing customer {customer.get('Customer_ID')}: {str(e)}")
                continue


        conn.commit()
        cursor.close()
        conn.close()


        return jsonify({
            'success': True,
            'processed': processed_count,
            'message': f"Successfully updated {processed_count} customers"
        })

    except Exception as e:
        print(f"Global error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/customers', methods=['GET'])
def get_customers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Handle optional pagination
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10000))
        offset = (page - 1) * size

        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM customers;")
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result else 0

        # Fetch customers
        cursor.execute("""
            SELECT
                Customer_ID as customer_id,
                Age as age,
                Gender as gender,
                District as district,
                Region as region,
                Location_Type as location_type,
                Customer_Type as customer_type,
                Employment_Status as employment_status,
                Income_Level as income_level,
                Education_Level as education_level,
                Tenure as tenure,
                Balance as balance,
                Credit_Score as credit_score,
                Outstanding_Loans as outstanding_loans,
                Num_Of_Products as num_of_products,
                Mobile_Banking_Usage as mobile_banking_usage,
                Number_of_Transactions_per_Month as number_of_transactions_per_month,
                Num_Of_Complaints as num_of_complaints,
                Proximity_to_NearestBranch_or_ATM_km as proximity_to_nearestbranch_or_atm_km,
                Mobile_Network_Quality as mobile_network_quality,
                Owns_Mobile_Phone as owns_mobile_phone,
                prediction,
                Churn_Probability as churn_probability
            FROM customers
            ORDER BY Customer_ID ASC
            LIMIT %s OFFSET %s;
        """, (size, offset))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "total": total,
            "customers": rows
        })

    except Exception as e:
        print("Error fetching customers:", str(e))
        return jsonify({"error": str(e)}), 500

    
@app.route('/api/customers/churn_count', methods=['GET'])
def churn_count():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        
        cursor.execute("""
            SELECT COUNT(*) as churn_count
            FROM customers
            WHERE prediction = 1
        """)
        
        result = cursor.fetchone()
        churn_count = result['churn_count'] if result else 0
        # Close the cursor
        cursor.close()
        
        return jsonify({'churn_count': churn_count})
    
    except Exception as e:
        print("Error fetching churn count:", str(e))
        return jsonify({'error': str(e)}), 500
#
@app.route('/api/customers/churn_summary', methods=['GET'])
def churn_summary():
    try:
        conn = get_db_connection()
        cursor = conn.cursor() 

        # Get total churners once
        cursor.execute("""
            SELECT COUNT(*) as total_churners
            FROM customers
            WHERE prediction = 1
        """)
        total_churners = cursor.fetchone()['total_churners'] or 0

        if total_churners == 0:
            return jsonify({})  # No churners

        attributes = [
            'Mobile_Banking_Usage',
            'Mobile_Network_Quality',
            'Num_Of_Complaints',
            'Proximity_to_NearestBranch_or_ATM_km',
            'Education_Level',
            'District',
            'Location_Type',
            'Region',
            'Employment_Status',
            'Num_Of_Products'
        ]

        summary = {}

        for attr in attributes:

            if attr == 'Proximity_to_NearestBranch_or_ATM_km':
                query = """
                    SELECT
                        CASE
                            WHEN Proximity_to_NearestBranch_or_ATM_km BETWEEN 0.5 AND 16 THEN '0.5 - 16 km'
                            WHEN Proximity_to_NearestBranch_or_ATM_km BETWEEN 17 AND 32 THEN '17 - 32 km'
                            WHEN Proximity_to_NearestBranch_or_ATM_km BETWEEN 33 AND 50 THEN '33 - 50 km'
                            ELSE 'Unknown'
                        END AS value,
                        COUNT(*) as churners
                    FROM customers
                    WHERE prediction = 1
                    GROUP BY value
                    ORDER BY churners DESC
                """
            else:
                query = f"""
                    SELECT {attr} AS value, COUNT(*) AS churners
                    FROM customers
                    WHERE prediction = 1
                    GROUP BY {attr}
                    ORDER BY churners DESC
                """

            cursor.execute(query)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                percentage = (row['churners'] / total_churners) * 100
                result.append({
                    "value": row['value'],
                    "churners": row['churners'],
                    "percentage": round(percentage, 2)
                })

            summary[attr] = result

        cursor.close()
        return jsonify(summary)

    except Exception as e:
        print("Error generating churn summary:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/customers/predicted")
def predicted_customers():
    threshold = request.args.get("threshold", default=50, type=int)

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
        SELECT * FROM customers
        WHERE prediction = 1
        AND churn_probability >= %s
        ORDER BY churn_probability DESC
    """
    cursor.execute(query, (threshold / 100.0,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(rows)

@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']

        # Read CSV to DataFrame
        df = pd.read_csv(file, encoding='utf-8')

        # Required columns
        required_columns = [
            'Age', 'Gender', 'District', 'Region', 'Location_Type',
            'Customer_Type', 'Employment_Status', 'Income_Level',
            'Education_Level', 'Tenure', 'Balance', 'Credit_Score',
            'Outstanding_Loans', 'Num_Of_Products',
            'Mobile_Banking_Usage', 'Number_of_Transactions_per_Month',
            'Num_Of_Complaints', 'Proximity_to_NearestBranch_or_ATM_km',
            'Mobile_Network_Quality', 'Owns_Mobile_Phone'
        ]

        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            return jsonify({"error": f"Missing columns: {', '.join(missing_cols)}"}), 400

        # Mapping dictionaries
        gender_map = {'Male': 1, 'Female': 0}
        region_map = {'Southern': 0, 'Northern': 1, 'Central': 2}
        location_type_map = {'Rural': 0, 'Urban': 1, 'Semi Urban': 2}
        customer_type_map = {'Retail': 0, 'SME': 1, 'Corporate': 2}
        employment_status_map = {'Self Employed': 0, 'Not Employed': 1, 'Employed': 2}
        education_level_map = {'Primary': 0, 'Secondary': 1, 'Tertiary': 2}
        mobile_banking_map = {'No': 0, 'Yes': 1}
        net_quality_map = {'Fair': 0, 'Poor': 1, 'Good': 2}
        owns_phone_map = {'Yes': 0, 'No': 1}

        # District mapping (example)
        district_map = {
            'Dedza': 6, 'Dowa': 26, 'Kasungu': 10, 'Lilongwe': 22, 'Mchinji': 8,
            'Nkhotakota': 12, 'Ntcheu': 27, 'Ntchisi': 9, 'Salima': 21,
            'Chitipa': 11, 'Karonga': 5, 'Likoma': 20, 'Mzimba': 16,
            'Nkhata Bay': 3, 'Rumphi': 24, 'Balaka': 25, 'Blantyre': 17,
            'Chikwawa': 2, 'Chiradzulu': 7, 'Machinga': 4, 'Mangochi': 14,
            'Mulanje': 15, 'Mwanza': 23, 'Nsanje': 18, 'Thyolo': 1,
            'Phalombe': 19, 'Zomba': 0, 'Neno': 13
        }

        # Map textual columns
        df['Gender'] = df['Gender'].map(gender_map)
        df['Region'] = df['Region'].map(region_map)
        df['Location_Type'] = df['Location_Type'].map(location_type_map)
        df['Customer_Type'] = df['Customer_Type'].map(customer_type_map)
        df['Employment_Status'] = df['Employment_Status'].map(employment_status_map)
        df['Education_Level'] = df['Education_Level'].map(education_level_map)
        df['Mobile_Banking_Usage'] = df['Mobile_Banking_Usage'].map(mobile_banking_map)
        df['Mobile_Network_Quality'] = df['Mobile_Network_Quality'].map(net_quality_map)
        df['Owns_Mobile_Phone'] = df['Owns_Mobile_Phone'].map(owns_phone_map)
        df['District'] = df['District'].map(district_map)

        if df.isnull().any().any():
            return jsonify({"error": "Some values could not be mapped. Check spelling in your CSV."}), 400

        # Prepare features
        features = df[required_columns].values

        probabilities = model.predict_proba(features)

        output_rows = []

        for i, prob in enumerate(probabilities):
            prob_churn = float(prob[1])
            prediction = 1 if prob_churn >= 0.5 else 0
            prob_percentage = round(prob_churn * 100, 2)

            row = df.iloc[i].to_dict()
            row['prediction'] = prediction
            row['churn_probability'] = prob_percentage

            # Save to DB
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (
                    Age, Gender, District, Region, Location_Type, Customer_Type,
                    Employment_Status, Income_Level, Education_Level, Tenure,
                    Balance, Credit_Score, Outstanding_Loans, Num_Of_Products,
                    Mobile_Banking_Usage, Number_of_Transactions_per_Month,
                    Num_Of_Complaints, Proximity_to_NearestBranch_or_ATM_km,
                    Mobile_Network_Quality, Owns_Mobile_Phone,
                    prediction, Churn_Probability
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['Age'], row['Gender'], row['District'], row['Region'],
                row['Location_Type'], row['Customer_Type'], row['Employment_Status'],
                row['Income_Level'], row['Education_Level'], row['Tenure'],
                row['Balance'], row['Credit_Score'], row['Outstanding_Loans'],
                row['Num_Of_Products'], row['Mobile_Banking_Usage'],
                row['Number_of_Transactions_per_Month'], row['Num_Of_Complaints'],
                row['Proximity_to_NearestBranch_or_ATM_km'], row['Mobile_Network_Quality'],
                row['Owns_Mobile_Phone'], prediction, prob_churn
            ))
            conn.commit()
            cursor.close()
            conn.close()

            output_rows.append(row)

        return jsonify({
            "message": f"Batch upload complete. {len(output_rows)} customers added.",
            "customers": output_rows
        })

    except Exception as e:
        print("Batch prediction error:", str(e))
        return jsonify({"error": f"Batch prediction failed: {str(e)}"}), 500

@app.route('/churn_summary')
def churn_summary_page():   
    """
    Render the churn summary page with data visualizations.
    """
    try:
        # Create a database cursor
        conn = get_db_connection()
        cursor = conn.cursor()

        # Execute query to get total churn count
        cursor.execute("SELECT COUNT(*) as churn_count FROM customers WHERE prediction ='will leave'")
        churn_count_result = cursor.fetchone()
        churn_count = churn_count_result['churn_count'] if churn_count_result else 0

        # Close the cursor
        cursor.close()

        # Render template with churn count
        return render_template('churn_summary.html', churn_count=churn_count)

    except Exception as e:
        print("Database error:", str(e))
        return render_template('churn_summary.html', churn_count=0, error=str(e))            
if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')
    