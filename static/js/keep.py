from flask import Flask, request, jsonify
import pandas as pd
import joblib
from database import get_db_connection  # Assuming you have this setup

app = Flask(__name__)

# Load your model
model = joblib.load('churn_model.pkl')

@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Read CSV file
        try:
            df = pd.read_csv(file)
        except Exception as e:
            return jsonify({"error": f"Could not read CSV: {str(e)}"}), 400

        # Required columns
        required_columns = [
            'Age', 'Gender', 'District', 'Region', 'Location_Type',
            'Customer_Type', 'Employment_Status', 'Income_Level',
            'Education_Level', 'Tenure', 'Balance', 'Credit_Score',
            'Outstanding_Loans', 'Num_Of_Products', 'Mobile_Banking_Usage',
            'Number_of_Transactions_per_Month', 'Num_Of_Complaints',
            'Proximity_to_NearestBranch_or_ATM_km', 'Mobile_Network_Quality',
            'Owns_Mobile_Phone'
        ]

        # Check for missing columns
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
        district_map = {
            'Dedza': 6, 'Dowa': 26, 'Kasungu': 10, 'Lilongwe': 22, 'Mchinji': 8,
            'Nkhotakota': 12, 'Ntcheu': 27, 'Ntchisi': 9, 'Salima': 21,
            'Chitipa': 11, 'Karonga': 5, 'Likoma': 20, 'Mzimba': 16,
            'Nkhata Bay': 3, 'Rumphi': 24, 'Balaka': 25, 'Blantyre': 17,
            'Chikwawa': 2, 'Chiradzulu': 7, 'Machinga': 4, 'Mangochi': 14,
            'Mulanje': 15, 'Mwanza': 23, 'Nsanje': 18, 'Thyolo': 1,
            'Phalombe': 19, 'Zomba': 0, 'Neno': 13
        }

        # Apply mappings
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

        # Check for any null values after mapping
        if df.isnull().any().any():
            return jsonify({"error": "Some values could not be mapped. Check your CSV data."}), 400

        # Prepare features for prediction
        features = df[required_columns].values
        probabilities = model.predict_proba(features)

        # Prepare response and save to database
        output = []
        conn = get_db_connection()
        cursor = conn.cursor()

        for i, prob in enumerate(probabilities):
            churn_prob = float(prob[1])
            prediction = 1 if churn_prob >= 0.5 else 0
            prob_percentage = round(churn_prob * 100, 2)

            # Add to output
            row = df.iloc[i].to_dict()
            row['Prediction'] = prediction
            row['Churn_Probability'] = prob_percentage
            output.append(row)

            # Save to database
            cursor.execute("""
                INSERT INTO customers (
                    Age, Gender, District, Region, Location_Type, Customer_Type,
                    Employment_Status, Income_Level, Education_Level, Tenure,
                    Balance, Credit_Score, Outstanding_Loans, Num_Of_Products,
                    Mobile_Banking_Usage, Number_of_Transactions_per_Month,
                    Num_Of_Complaints, Proximity_to_NearestBranch_or_ATM_km,
                    Mobile_Network_Quality, Owns_Mobile_Phone,
                    Prediction, Churn_Probability
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['Age'], row['Gender'], row['District'], row['Region'],
                row['Location_Type'], row['Customer_Type'], row['Employment_Status'],
                row['Income_Level'], row['Education_Level'], row['Tenure'],
                row['Balance'], row['Credit_Score'], row['Outstanding_Loans'],
                row['Num_Of_Products'], row['Mobile_Banking_Usage'],
                row['Number_of_Transactions_per_Month'], row['Num_Of_Complaints'],
                row['Proximity_to_NearestBranch_or_ATM_km'], row['Mobile_Network_Quality'],
                row['Owns_Mobile_Phone'], prediction, churn_prob
            ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "processed_count": len(output),
            "customers": output
        })

    except Exception as e:
        print("Batch prediction error:", str(e))
        return jsonify({"error": f"Batch prediction failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
    
    from flask import request, jsonify
import numpy as np
import pandas as pd

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
        
document.addEventListener('DOMContentLoaded', function () {
    const predictBtn = document.getElementById('predict-btn');
    const form = document.getElementById('customer-form');
    const resultArea = document.getElementById('resultArea');

    const districtRegionMap = {
        'Dedza': 'Central', 'Dowa': 'Central', 'Kasungu': 'Central', 'Lilongwe': 'Central',
        'Mchinji': 'Central', 'Nkhotakota': 'Central', 'Ntcheu': 'Central', 'Ntchisi': 'Central',
        'Salima': 'Central', 'Chitipa': 'Northern', 'Karonga': 'Northern', 'Likoma': 'Northern',
        'Mzimba': 'Northern', 'Nkhata Bay': 'Northern', 'Rumphi': 'Northern',
        'Balaka': 'Southern', 'Blantyre': 'Southern', 'Chikwawa': 'Southern',
        'Chiradzulu': 'Southern', 'Machinga': 'Southern', 'Mangochi': 'Southern',
        'Mulanje': 'Southern', 'Mwanza': 'Southern', 'Nsanje': 'Southern', 'Thyolo': 'Southern',
        'Phalombe': 'Southern', 'Zomba': 'Southern', 'Neno': 'Southern'
    };

    document.getElementById("entry-type").addEventListener("change", function() {
        const single = document.getElementById("single-entry-fields");
        const multiple = document.getElementById("multiple-entry-fields");

        if (this.value === "multiple") {
            single.style.display = "none";
            multiple.style.display = "block";
        } else {
            single.style.display = "block";
            multiple.style.display = "none";
        }
    });

    predictBtn.addEventListener('click', async function (event) {
        event.preventDefault();

        const entryType = document.getElementById("entry-type").value;

        if (entryType === "single") {
            if (!validateForm()) return;
            await submitSingleCustomer();
        } else if (entryType === "multiple") {
            await submitMultipleCustomers();
        } else {
            resultArea.innerHTML = `<p class="text-red-600">Please select Entry Type.</p>`;
        }
    });

    async function submitSingleCustomer() {
        const regionMap = { 'Southern': 0, 'Northern': 1, 'Central': 2 };
        const genderMap = { 'Male': 1, 'Female': 0 };
        const districtMap = {
            "Dedza": 6, "Dowa": 26, "Kasungu": 10, "Lilongwe": 22, "Mchinji": 8, "Nkhotakota": 12,
            "Ntcheu": 27, "Ntchisi": 9, "Salima": 21, "Chitipa": 11, "Karonga": 5, "Likoma": 20,
            "Mzimba": 16, "Nkhata Bay": 3, "Rumphi": 24, "Balaka": 25, "Blantyre": 17, "Chikwawa": 2,
            "Chiradzulu": 7, "Machinga": 4, "Mangochi": 14, "Mulanje": 15, "Mwanza": 23,
            "Nsanje": 18, "Thyolo": 1, "Phalombe": 19, "Zomba": 0, "Neno": 13
        };
        const customertypeMap = { 'Retail': 0, 'SME': 1, 'Corporate': 2 };
        const employmentstatusMap = { 'Self Employed': 0, 'Not Employed': 1, 'Employed': 2 };
        const educationlevelMap = { 'Primary': 0, 'Secondary': 1, 'Tertiary': 2 };
        const netqualityMap = { 'Fair': 0, 'Poor': 1, 'Good': 2 };
        const phoneMap = { 'Yes': 0, 'No': 1 };
        const mobileBankMap = { 'No': 0, 'Yes': 1 };
        const locationtypeMap = { 'Rural': 0, 'Urban': 1, 'Semi Urban': 2 };

        const formData = {
            Age: parseInt(document.getElementById('age').value),
            Gender: genderMap[document.getElementById('gender').value],
            District: districtMap[document.getElementById('district').value],
            Region: regionMap[document.getElementById('region').value],
            Location_Type: locationtypeMap[document.getElementById('location-type').value],
            Customer_Type: customertypeMap[document.getElementById('customer-type').value],
            Employment_Status: employmentstatusMap[document.getElementById('employment-status').value],
            Income_Level: parseFloat(document.getElementById('income-level').value),
            Education_Level: educationlevelMap[document.getElementById('education-level').value],
            Tenure: parseInt(document.getElementById('tenure').value),
            Balance: parseFloat(document.getElementById('balance').value),
            Credit_Score: parseInt(document.getElementById('credit-score').value),
            Outstanding_Loans: parseFloat(document.getElementById('outstanding-loans').value),
            Num_Of_Products: parseInt(document.getElementById('num-of-products').value),
            Mobile_Banking_Usage: mobileBankMap[document.getElementById('mobile-banking-usage').value],
            Number_of_Transactions_per_Month: parseInt(document.getElementById('transactions-per-month').value),
            Num_Of_Complaints: parseInt(document.getElementById('num-of-complaints').value),
            Proximity_to_NearestBranch_or_ATM_km: parseFloat(document.getElementById('proximity-to-branch').value),
            Mobile_Network_Quality: netqualityMap[document.getElementById('mobile-network-quality').value],
            Owns_Mobile_Phone: phoneMap[document.getElementById('owns-mobile-phone').value]
        };

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                resultArea.innerHTML = `<p class="text-green-600">✅ Customer added successfully.<br>Estimated churn risk: <strong>${result.probability}%</strong></p>`;
                form.reset();
            } else {
                resultArea.innerHTML = `<p class="text-red-600">${result.error}</p>`;
            }
        } catch (error) {
            console.error("Prediction Error:", error);
            resultArea.innerHTML = `<p class="text-red-600">Something went wrong. Try again.</p>`;
        }
    }

    async function submitMultipleCustomers() {
        const fileInput = document.getElementById("batch-upload");
        if (!fileInput.files.length) {
            resultArea.innerHTML = `<p class="text-red-600">⚠️ Please upload a CSV file.</p>`;
            return;
        }

        const file = fileInput.files[0];
        const text = await file.text();

        try {
            const response = await fetch('/predict_batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ csv_content: text })
            });

            const result = await response.json();

            if (result.success) {
                resultArea.innerHTML = `<p class="text-green-600">✅ ${result.inserted_count} customers were added successfully.</p>`;
                form.reset();
            } else {
                resultArea.innerHTML = `<p class="text-red-600">${result.error}</p>`;
            }
        } catch (error) {
            console.error("Batch Upload Error:", error);
            resultArea.innerHTML = `<p class="text-red-600">Something went wrong while uploading.</p>`;
        }
    }

    function validateForm() {
        const requiredFields = [
            'age', 'gender', 'district', 'region', 'location-type', 'customer-type', 'employment-status',
            'income-level', 'education-level', 'tenure', 'balance', 'credit-score', 'outstanding-loans',
            'num-of-products', 'mobile-banking-usage', 'transactions-per-month', 'num-of-complaints',
            'proximity-to-branch', 'mobile-network-quality', 'owns-mobile-phone'
        ];
        let isValid = true;
        requiredFields.forEach(id => {
            const el = document.getElementById(id);
            if (el && !el.value) {
                el.style.borderColor = 'red';
                isValid = false;
            } else if (el) {
                el.style.borderColor = '';
            }
        });

        if (!isValid) {
            resultArea.innerHTML = '<p class="text-red-600">⚠️ Please fill all required fields.</p>';
        }

        return isValid;
    }
});



<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Customer Data Import</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .left-panel {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        h2 {
            color: #333;
            margin-bottom: 20px;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        
        input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 2px dashed #ddd;
            border-radius: 5px;
            cursor: pointer;
            transition: border-color 0.3s;
        }
        
        input[type="file"]:hover {
            border-color: #007bff;
        }
        
        .help-text {
            color: #666;
            font-style: italic;
            margin-top: 5px;
        }
        
        .import-button {
            background-color: #007bff;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        
        .import-button:hover {
            background-color: #0056b3;
        }
        
        .import-button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        
        .status-area {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }
        
        .progress-container {
            background-color: #e9ecef;
            border-radius: 10px;
            height: 20px;
            margin-bottom: 10px;
            overflow: hidden;
        }
        
        .progress-bar {
            height: 100%;
            background-color: #007bff;
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 10px;
        }
        
        .status-message {
            font-weight: bold;
            color: #333;
        }
        
        .error {
            color: #dc3545;
        }
        
        .success {
            color: #28a745;
        }
        
        .results-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #333;
        }
        
        tr:hover {
            background-color: #f8f9fa;
        }
        
        .prediction-1 {
            background-color: #ffe6e6;
        }
        
        .prediction-0 {
            background-color: #e6ffe6;
        }
    </style>
</head>
<body>
    <div class="left-panel">
        <h2>Import Customer Data</h2>
        <form id="customer-import-form">
            <div class="form-group">
                <label for="csv-import">Upload CSV File:</label>
                <input type="file" id="csv-import" accept=".csv" required>
                <p class="help-text"><small>Upload CSV file containing customer data to import into the database</small></p>
            </div>
            <button type="button" id="import-btn" class="import-button">Import Data</button>
            <div id="import-status" class="status-area">
                <div class="progress-container">
                    <div class="progress-bar"></div>
                </div>
                <div class="status-message">Ready to import</div>
            </div>
        </form>
    </div>
    


    <script>
        document.addEventListener("DOMContentLoaded", () => {
            const importButton = document.getElementById("import-btn");
            const fileInput = document.getElementById("csv-import");
            const progressBar = document.querySelector(".progress-bar");
            const statusMessage = document.querySelector(".status-message");

            importButton.addEventListener("click", () => {
                const file = fileInput.files[0];
                if (!file) {
                    alert("Please choose a CSV file.");
                    return;
                }

                const formData = new FormData();
                formData.append("file", file);

                // Reset UI
                importButton.disabled = true;
                statusMessage.textContent = "Uploading...";
                statusMessage.className = "status-message";
                progressBar.style.width = "30%";

                fetch("/predict/batch", {
                    method: "POST",
                    body: formData
                })
                .then(response => {
                    progressBar.style.width = "60%";
                    if (!response.ok) {
                        throw new Error("Server returned an error.");
                    }
                    return response.json();
                })
                .then(data => {
                    progressBar.style.width = "100%";
                    
                    if (data.error) {
                        statusMessage.textContent = `Error: ${data.error}`;
                        statusMessage.className = "status-message error";
                    } else {
                        statusMessage.textContent = data.message;
                        statusMessage.className = "status-message success";
                        
                        // Clear the file input after successful upload
                        fileInput.value = "";
                        
                        // Reset progress bar after a short delay
                        setTimeout(() => {
                            progressBar.style.width = "0%";
                            statusMessage.textContent = "Ready to import";
                            statusMessage.className = "status-message";
                        }, 3000);
                    }
                })
                .catch(error => {
                    progressBar.style.width = "100%";
                    statusMessage.textContent = `Upload failed: ${error.message}`;
                    statusMessage.className = "status-message error";
                })
                .finally(() => {
                    importButton.disabled = false;
                });
            });
        });
    </script>
</body>
</html>




document.addEventListener('DOMContentLoaded', function() {
    // Debug: Confirm script is loading
    console.log("Script loaded successfully");

    // District-Region mapping from your second script
    const districtRegionMap = {
        'Dedza': 'Central', 'Dowa': 'Central', 'Kasungu': 'Central', 
        'Lilongwe': 'Central', 'Mchinji': 'Central', 'Nkhotakota': 'Central', 
        'Ntcheu': 'Central', 'Ntchisi': 'Central', 'Salima': 'Central',
        'Chitipa': 'Northern', 'Karonga': 'Northern', 'Likoma': 'Northern',
        'Mzimba': 'Northern', 'Nkhata Bay': 'Northern', 'Rumphi': 'Northern',
        'Balaka': 'Southern', 'Blantyre': 'Southern', 'Chikwawa': 'Southern',
        'Chiradzulu': 'Southern', 'Machinga': 'Southern', 'Mangochi': 'Southern',
        'Mulanje': 'Southern', 'Mwanza': 'Southern', 'Nsanje': 'Southern',
        'Thyolo': 'Southern', 'Phalombe': 'Southern', 'Zomba': 'Southern', 
        'Neno': 'Southern'
    };

    // Initialize district/region dropdowns
    const allDistricts = Object.keys(districtRegionMap);
    const districtSelect = document.getElementById("district");
    const regionSelect = document.getElementById("region");

    function populateDistricts(districts, selected = "") {
        districtSelect.innerHTML = `<option value="" disabled ${selected === "" ? "selected" : ""}>Select District</option>`;
        districts.forEach(d => {
            const opt = document.createElement("option");
            opt.value = d;
            opt.textContent = d;
            if (d === selected) opt.selected = true;
            districtSelect.appendChild(opt);
        });
    }

    // District selection handler
    districtSelect.addEventListener("change", function() {
        const selectedDistrict = this.value;
        regionSelect.value = districtRegionMap[selectedDistrict];
    });

    // Region selection handler
    regionSelect.addEventListener("change", function() {
        const selectedRegion = this.value;
        const filteredDistricts = allDistricts.filter(d => districtRegionMap[d] === selectedRegion);
        populateDistricts(filteredDistricts);
    });

    // Initial load
    populateDistricts(allDistricts);