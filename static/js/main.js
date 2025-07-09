
document.addEventListener('DOMContentLoaded', function () {
    const slider = document.getElementById('probability-slider');
    const valueSpan = document.getElementById('probability-value');
    const vapan = document.getElementById('threshold-display');
    slider.addEventListener('input', function () {
        valueSpan.textContent = slider.value + '%';
        vapan.textContent = slider.value + '%';
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const slider = document.getElementById("probability-slider");
    const probabilityValue = document.getElementById("probability-value");
    const totalCountDisplay = document.getElementById("total-count-display");
    const exportBtn = document.getElementById("export-btn");
    const resultsBody = document.getElementById("results-body");

    // Lookup tables for human-friendly labels
    const genderMap = { 0: "Female", 1: "Male" };
    const regionMap = { 0: "Southern", 1: "Northern", 2: "Central" };
    const customerTypeMap = { 0: "Retail", 1: "SME", 2: "Corporate" };
    const employmentStatusMap = { 0: "Self Employed", 1: "Not Employed", 2: "Employed" };
    const educationLevelMap = { 0: "Primary", 1: "Secondary", 2: "Tertiary" };
    const netQualityMap = { 0: "Fair", 1: "Poor", 2: "Good" };
    const phoneMap = { 0: "Yes", 1: "No" };
    const mobileBankMap = { 0: "No", 1: "Yes" };
    const locationTypeMap = { 0: "Rural", 1: "Urban", 2: "Semi Urban" };

    const districtMap = {
        0: "Zomba", 1: "Thyolo", 2: "Chikwawa", 3: "Nkhata Bay", 4: "Machinga",
        5: "Karonga", 6: "Dedza", 7: "Chiradzulu", 8: "Mchinji", 9: "Ntchisi",
        10: "Kasungu", 11: "Chitipa", 12: "Nkhotakota", 13: "Neno", 14: "Mangochi",
        15: "Mulanje", 16: "Mzimba", 17: "Blantyre", 18: "Nsanje", 19: "Phalombe",
        20: "Likoma", 21: "Salima", 22: "Lilongwe", 23: "Mwanza", 24: "Rumphi",
        25: "Balaka", 26: "Dowa", 27: "Ntcheu", 28: "Unknown", 29: "Unknown"
    };

    function loadCustomers(threshold) {
        fetch(`/api/customers/predicted?threshold=${threshold}`)
            .then(response => response.json())
            .then(data => {
                resultsBody.innerHTML = "";

                totalCountDisplay.textContent =
                    `Total customers with ≥ ${threshold}% probability of leaving: ${data.length}`;
                probabilityValue.textContent = `${threshold}%`;

                if (data.length === 0) {
                    resultsBody.innerHTML = `
                        <tr>
                            <td colspan="23" style="text-align:center; color: #666;">
                                No customers found above this probability.
                            </td>
                        </tr>`;
                    return;
                }

                for (const customer of data) {
                    const row = document.createElement("tr");
                    row.className = "border-b hover:bg-gray-50";

                    row.innerHTML = `
                        <td class="p-3">${customer.customer_id ?? ""}</td>
                        <td class="p-3">${customer.age ?? ""}</td>
                        <td class="p-3">${genderMap[customer.gender] ?? customer.gender}</td>
                        <td class="p-3">${districtMap[customer.district] ?? customer.district}</td>
                        <td class="p-3">${regionMap[customer.region] ?? customer.region}</td>
                        <td class="p-3">${locationTypeMap[customer.location_type] ?? customer.location_type}</td>
                        <td class="p-3">${customerTypeMap[customer.customer_type] ?? customer.customer_type}</td>
                        <td class="p-3">${employmentStatusMap[customer.employment_status] ?? customer.employment_status}</td>
                        <td class="p-3">${customer.income_level ?? ""}</td>
                        <td class="p-3">${educationLevelMap[customer.education_level] ?? customer.education_level}</td>
                        <td class="p-3">${customer.tenure ?? ""}</td>
                        <td class="p-3">${customer.balance ?? ""}</td>
                        <td class="p-3">${customer.credit_score ?? ""}</td>
                        <td class="p-3">${customer.outstanding_loans ?? ""}</td>
                        <td class="p-3">${customer.num_of_products ?? ""}</td>
                        <td class="p-3">${mobileBankMap[customer.mobile_banking_usage] ?? customer.mobile_banking_usage}</td>
                        <td class="p-3">${customer.number_of_transactions_per_month ?? ""}</td>
                        <td class="p-3">${customer.num_of_complaints ?? ""}</td>
                        <td class="p-3">${customer.proximity_to_nearestbranch_or_atm_km ?? ""}</td>
                        <td class="p-3">${netQualityMap[customer.mobile_network_quality] ?? customer.mobile_network_quality}</td>
                        <td class="p-3">${phoneMap[customer.owns_mobile_phone] ?? customer.owns_mobile_phone}</td>
                        <td class="p-3">${
                            customer.prediction === 1
                                ? '<span class="text-red-600">Will Leave</span>'
                                : customer.prediction === 0
                                    ? '<span class="text-green-600">Will Stay</span>'
                                    : ''
                        }</td>
                        <td class="p-3">${
                            customer.churn_probability !== null && customer.churn_probability !== undefined
                                ? (parseFloat(customer.churn_probability) * 100).toFixed(2) + "%"
                                : ""
                        }</td>
                    `;
                    resultsBody.appendChild(row);
                }
            })
            .catch(error => {
                console.error("Error fetching customers:", error);
            });
    }

    // Initial load
    loadCustomers(slider.value);

    slider.addEventListener("input", () => {
        loadCustomers(slider.value);
    });

    exportBtn.addEventListener("click", () => {
        const threshold = slider.value;
        let csvContent = "";

        csvContent += `"Customers with ≥ ${threshold}% Probability of Leaving"\n\n`;

        // Get table headers
        const headers = [];
        document.querySelectorAll("#results-table thead th").forEach(th => {
            headers.push(`"${th.textContent.trim()}"`);
        });
        csvContent += headers.join(",") + "\n";

        // Get table rows
        const rows = [];
        resultsBody.querySelectorAll("tr").forEach(tr => {
            const cells = [];
            tr.querySelectorAll("td").forEach(td => {
                let text = td.textContent.trim();
                text = text.replace(/"/g, '""'); // Escape quotes
                cells.push(`"${text}"`);
            });
            rows.push(cells.join(","));
        });

        if (rows.length === 0) {
            alert("No data to export.");
            return;
        }

        csvContent += rows.join("\n");

        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `customers_prob_${threshold}.csv`);
        link.click();
        URL.revokeObjectURL(url);
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const entryTypeSelect = document.getElementById("entry-type");
    const singleEntryFields = document.getElementById("single-entry-fields");
    const multipleEntryFields = document.getElementById("multiple-entry-fields");

    entryTypeSelect.addEventListener("change", function () {
        if (this.value === "single") {
            singleEntryFields.style.display = "block";
            multipleEntryFields.style.display = "none";
        } else if (this.value === "multiple") {
            singleEntryFields.style.display = "none";
            multipleEntryFields.style.display = "block";
        }
    });

    // Handle CSV upload
    const fileInput = document.getElementById("batch-upload");
    fileInput.addEventListener("change", function () {
        const file = this.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function (e) {
            const csvText = e.target.result;
            processCsv(csvText);
        };
        reader.readAsText(file);
    });

    function processCsv(csvText) {
        // Parse CSV text → array of objects
        const rows = csvText.trim().split("\n");
        const headers = rows.shift().split(",").map(h => h.trim());
        const customers = rows.map(line => {
            const values = line.split(",");
            const obj = {};
            headers.forEach((h, i) => {
                obj[h] = values[i] !== undefined ? values[i].trim() : "";
            });
            return obj;
        });

        console.log("Parsed CSV:", customers);

        // Send all customers to backend
        fetch("/predict_batch", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(customers)
        })
        .then(res => res.json())
        .then(response => {
            alert(`Batch upload complete. ${response.processed} customers added!`);
        })
        .catch(err => {
            console.error(err);
            alert("Batch upload failed.");
        });
    }
});
document.addEventListener("DOMContentLoaded", () => {
    fetch("/api/customers")
        .then(response => response.json())
        .then(data => {
            document.getElementById("total-customers").textContent = data.total;
        })
        .catch(err => {
            console.error(err);
            document.getElementById("total-customers").textContent = "Error loading";
        });
});

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
// This script handles the customer data loading and display on the main page
