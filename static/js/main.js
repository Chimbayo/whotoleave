
document.addEventListener('DOMContentLoaded', function () {
    const slider = document.getElementById('probability-slider');
    const valueSpan = document.getElementById('probability-value');
    const vapan = document.getElementById('threshold-display');
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

    slider.addEventListener('input', function () {
        valueSpan.textContent = slider.value + '%';
        vapan.textContent = slider.value + '%';
        loadCustomers(slider.value);
    });

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
                            <td colspan="23" style="text-align:center; color: #666; padding: 40px; font-style: italic;">
                                No customers found above this probability threshold.
                            </td>
                        </tr>`;
                    return;
                }

                for (const customer of data) {
                    const row = document.createElement("tr");
                    const probability = parseFloat(customer.churn_probability) * 100;
                    const isHighRisk = probability >= 50;
                    
                    row.className = isHighRisk ? "high-risk-row" : "low-risk-row";

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
                        <td class="p-3">${customer.proximity_to_nearestbranch_or_atm_km ? parseFloat(customer.proximity_to_nearestbranch_or_atm_km).toFixed(1) + ' km' : ""}</td>
                        <td class="p-3">${netQualityMap[customer.mobile_network_quality] ?? customer.mobile_network_quality}</td>
                        <td class="p-3">${phoneMap[customer.owns_mobile_phone] ?? customer.owns_mobile_phone}</td>
                        <td class="p-3">${
                            customer.prediction === 1
                                ? '<span class="prediction-churn">Will Leave</span>'
                                : customer.prediction === 0
                                    ? '<span class="prediction-stay">Will Stay</span>'
                                    : ''
                        }</td>
                        <td class="p-3">${
                            customer.churn_probability !== null && customer.churn_probability !== undefined
                                ? `<span class="${isHighRisk ? 'probability-high' : 'probability-low'}">${probability.toFixed(1)}%</span>`
                                : ""
                        }</td>
                    `;
                    resultsBody.appendChild(row);
                }

                addZebraStriping();
            })
            .catch(error => {
                console.error("Error fetching customers:", error);
                resultsBody.innerHTML = `
                    <tr>
                        <td colspan="23" style="text-align:center; color: #ef4444; padding: 40px;">
                            Loading customer data. 
                        </td>
                    </tr>`;
            });
    }

    function addZebraStriping() {
        const rows = resultsBody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            row.classList.remove('zebra-even', 'zebra-odd');
            if (index % 2 === 0) {
                row.classList.add('zebra-even');
            } else {
                row.classList.add('zebra-odd');
            }
        });
    }

    // Initial load
    loadCustomers(slider.value);

    // Auto-refresh every 5 seconds
    setInterval(() => {
        loadCustomers(slider.value);
    }, 5000);

    exportBtn.addEventListener("click", () => {
        const threshold = slider.value;
        let csvContent = "";

        csvContent += `"Customers with ≥ ${threshold}% Probability of Leaving"\n\n`;

        const headers = [];
        document.querySelectorAll("#results-table thead th").forEach(th => {
            headers.push(`"${th.textContent.trim()}"`);
        });
        csvContent += headers.join(",") + "\n";

        const rows = [];
        resultsBody.querySelectorAll("tr").forEach(tr => {
            const cells = [];
            tr.querySelectorAll("td").forEach(td => {
                let text = td.textContent.trim();
                text = text.replace(/"/g, '""');
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
        link.setAttribute("download", `customers_high_risk_${threshold}percent.csv`);
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
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

    function refreshTotalCustomers() {
        fetch("/api/customers")
            .then(response => response.json())
            .then(data => {
                document.getElementById("total-customers").textContent = data.total;
            })
            .catch(err => {
                console.error(err);
                document.getElementById("total-customers").textContent = "Error loading";
            });
    }

    // Load initially
    refreshTotalCustomers();

    // Refresh every 10 seconds
    setInterval(refreshTotalCustomers, 5000);
});


// This script handles the customer data loading and display on the main page
