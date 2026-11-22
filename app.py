import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import random
import hashlib
import base64
import urllib.request
import json
from datetime import datetime

st.set_page_config(page_title="Loan Prediction System", layout="wide")
st.title("🏦 Loan Prediction & Analytics Dashboard")

CSV_FILE = "loan_dataset.csv"

# SET YOUR ADMIN USERNAME & PASSWORD HERE:
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Tanmay@2026"

PASSWORD_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def save_csv_permanently(df):
    df.to_csv(CSV_FILE, index=False)
    try:
        token = st.secrets.get("GITHUB_TOKEN", None)
        repo = st.secrets.get("GITHUB_REPO", "TanmayTiwari1620/loan-prediction-dataset")
        if token:
            api_url = f"https://github.com{repo}/contents/{CSV_FILE}"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                file_info = json.loads(resp.read().decode())
                sha = file_info["sha"]

            with open(CSV_FILE, "rb") as f:
                content_b64 = base64.b64encode(f.read()).decode()

            payload = json.dumps({
                "message": "Log new visitor loan check",
                "content": content_b64,
                "sha": sha
            }).encode()

            put_req = urllib.request.Request(api_url, data=payload, headers=headers, method="PUT")
            urllib.request.urlopen(put_req)
    except Exception:
        pass

with st.sidebar:
    st.header("🔐 Admin Access Only")
    if not st.session_state.authenticated:
        st.caption("Dataset and Pie Charts are locked. Enter admin password to unlock.")
        user_input = st.text_input("Username", placeholder="Enter admin username")
        pass_input = st.text_input("Password", type="password", placeholder="Enter admin password")

        if st.button("🔓 Unlock Admin Tabs"):
            entered_hash = hashlib.sha256(pass_input.encode()).hexdigest()
            if user_input.strip() == ADMIN_USERNAME and entered_hash == PASSWORD_HASH:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Wrong Username or Password!")
    else:
        st.success("✅ Admin Unlocked")
        if st.button("🔒 Lock & Logout"):
            st.session_state.authenticated = False
            st.rerun()

tab1, tab2, tab3 = st.tabs(["➕ Check Loan Eligibility", "📋 Visitor Dataset (Locked)", "📊 Loan Pie Charts (Locked)"])

with tab1:
    st.subheader("Enter Applicant Details")
    col1, col2, col3 = st.columns(3)

    with col1:
        loan_id = st.text_input("Loan ID", value=f"LP{random.randint(1000, 9999)}")
        applicant_name = st.text_input("Applicant Name", placeholder="Enter your full name")
        gender = st.selectbox("Gender", ["Male", "Female"])
        married = st.selectbox("Married", ["Yes", "No"])
        dependents = st.selectbox("Dependents", ["0", "1", "2", "3+"])

    with col2:
        education = st.selectbox("Education", ["Graduated", "Not Graduated"])
        self_employed = st.selectbox("Self Employed", ["No", "Yes"])
        income = st.number_input("Applicant Monthly Income (₹)", min_value=0, value=100000)
        co_income = st.number_input("Co-applicant Monthly Income (₹)", min_value=0, value=25000)
        property_area = st.selectbox("Property Area", ["Urban", "Semiurban", "Rural"])

    with col3:
        loan_amt = st.number_input("Requested Loan Amount (₹)", min_value=0, value=200000)
        loan_term = st.selectbox("Loan Amount Term (Months)", options=[12,36,60,84,120,180,240,300,360], index=6)
        credit_history = st.selectbox("Credit History (1 = Good, 0 = Bad)", [1, 0])

    if st.button("Predict Loan Status"):
        display_name = applicant_name.strip() if applicant_name.strip() else "Anonymous Visitor"
        total_income = income + co_income

        dep_factor = 0.90 if dependents in ["2", "3+"] else 1.0
        edu_factor = 1.05 if education == "Graduated" else 0.95
        term_multiplier = min(loan_term * 0.45, 60)

        max_eligible_loan = int(total_income * term_multiplier * dep_factor * edu_factor) if credit_history == 1 else 0

        if credit_history == 1 and loan_amt <= max_eligible_loan:
            status = "Approved"
            st.success(f"✅ LOAN APPROVED for **{display_name}** (Loan ID: **{loan_id}**)")
            st.info(
                f"💰 **Approved Loan Amount:** ₹{loan_amt:,} (for {loan_term} months)\n\n"
                f"📈 **Maximum Loan You Can Get:** Up to **₹{max_eligible_loan:,}**"
            )
        else:
            status = "Rejected"
            st.error(f"❌ LOAN REJECTED for **{display_name}** (Loan ID: **{loan_id}**)")
            if credit_history == 0:
                st.warning("⚠️ **Reason:** Bad Credit History (0). Maximum eligible loan amount is **₹0**.")
            else:
                st.warning(
                    f"⚠️ **Reason:** Requested amount (₹{loan_amt:,}) exceeds your limit.\n\n"
                    f"💡 **Maximum Loan You Can Get:** Up to **₹{max_eligible_loan:,}**"
                )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_cols = [
            "Timestamp", "Loan_ID", "Applicant_Name", "Gender", "Married", "Dependents",
            "Education", "Self_Employed", "ApplicantIncome", "CoapplicantIncome",
            "LoanAmount", "Loan_Amount_Term", "Credit_History", "Property_Area",
            "Approved_Amount", "Loan_Status"
        ]

        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
        else:
            df = pd.DataFrame(columns=all_cols)

        new_row = {
            "Timestamp": timestamp,
            "Loan_ID": loan_id,
            "Applicant_Name": display_name,
            "Gender": gender,
            "Married": married,
            "Dependents": dependents,
            "Education": education,
            "Self_Employed": self_employed,
            "ApplicantIncome": income,
            "CoapplicantIncome": co_income,
            "LoanAmount": loan_amt,
            "Loan_Amount_Term": loan_term,
            "Credit_History": credit_history,
            "Property_Area": property_area,
            "Approved_Amount": max_eligible_loan,
            "Loan_Status": status
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_csv_permanently(df)

with tab2:
    st.subheader("🔒 Collected Visitor & Applicant Records")
    if not st.session_state.authenticated:
        st.error("⛔ **Protected Area:** Enter the Admin Password in the left sidebar to view visitor records.")
    else:
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            if "Loan_Status" in df.columns:
                df["Loan_Status"] = df["Loan_Status"].astype(str).str.strip().replace({"Y": "Approved", "N": "Rejected", "y": "Approved", "n": "Rejected"})

            col_s1, col_s2 = st.columns([3, 1])
            with col_s1:
                search_query = st.text_input("🔍 Search by Loan ID or Visitor Name", placeholder="Type name or LP1234...")
            with col_s2:
                st.write("")
                st.write("")
                csv_download = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", data=csv_download, file_name="visitor_loan_data.csv", mime="text/csv")

            if search_query.strip():
                mask = df.apply(lambda row: search_query.lower() in str(row.values).lower(), axis=1)
                st.dataframe(df[mask], use_container_width=True)
            else:
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("No visitor records found yet.")

with tab3:
    st.subheader("🔒 Loan Approval & Category Analytics")
    if not st.session_state.authenticated:
        st.error("⛔ **Protected Area:** Enter the Admin Password in the left sidebar to view pie charts.")
    else:
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            df.columns = df.columns.str.strip()

            status_col = next((c for c in df.columns if 'status' in c.lower()), None)
            amount_col = next((c for c in df.columns if c.lower() == 'loanamount' or ('amount' in c.lower() and 'approved' not in c.lower() and 'eligible' not in c.lower() and 'term' not in c.lower())), None)

            approved, rejected = 0, 0
            if status_col:
                vals = df[status_col].astype(str).str.strip().str.lower()
                approved = vals.isin(['y', 'yes', '1', 'approved']).sum()
                rejected = vals.isin(['n', 'no', '0', 'rejected']).sum()

            if approved + rejected == 0:
                approved, rejected = 80, 20

            amounts = pd.to_numeric(df[amount_col], errors='coerce').dropna().tolist() if amount_col else []
            if len(amounts) >= 3:
                amounts.sort()
                n = len(amounts)
                low = n // 3
                mid = (2 * n) // 3 - low
                high = n - low - mid
            else:
                low, mid, high = 20, 40, 40

            total_s = approved + rejected
            total_c = low + mid + high

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
            ax1.pie(
                [approved, rejected],
                labels=[f"Approved\n{approved/total_s*100:.0f}%", f"Rejected\n{rejected/total_s*100:.0f}%"],
                colors=['#1ea838', '#d94e43'],
                labeldistance=0.45,
                startangle=35,
                textprops={'color': 'white', 'weight': 'bold', 'fontsize': 11, 'ha': 'center'}
            )
            ax1.set_title("Loan Approval Status", fontsize=14, fontweight='bold')

            ax2.pie(
                [mid, low, high],
                labels=[f"Middle\n{mid/total_c*100:.0f}%", f"Low\n{low/total_c*100:.0f}%", f"High\n{high/total_c*100:.0f}%"],
                colors=['#eb9334', '#70499c', '#0b6ab3'],
                labeldistance=0.52,
                startangle=-30,
                textprops={'color': 'white', 'weight': 'bold', 'fontsize': 11, 'ha': 'center'}
            )
            ax2.set_title("Loan Category", fontsize=14, fontweight='bold')

            st.pyplot(fig)

tab1, tab2, tab3 = st.tabs(["➕ Check Loan Eligibility", "📋 Visitor Dataset (Locked)", "📊 Loan Pie Charts (Locked)"])
