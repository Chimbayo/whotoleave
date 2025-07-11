document.addEventListener("DOMContentLoaded", function () {
    // Mappings from codes to human-friendly labels
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

    fetch("/api/customers")
        .then(response => response.json())
        .then(data => {
            const customers = data.customers || [];
            const tbody = document.getElementById("results-body");
            tbody.innerHTML = "";

            for (const customer of customers) {
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
                    <td class="p-3">${customer.prediction ?? ""}</td>
                    <td class="p-3">${
                        customer.churn_probability !== null && customer.churn_probability !== undefined
                            ? (parseFloat(customer.churn_probability) * 100).toFixed(2) + "%"
                            : ""
                    }</td>
                `;

                tbody.appendChild(row);
            }

            console.log(`Loaded ${customers.length} customers.`);
        })
        .catch(error => {
            console.error("Error loading customer data:", error);
        });
});
