import streamlit as st
import pandas as pd
import random
import sqlite3
import time
from twilio.rest import Client
import plotly.graph_objects as go

# Initialize SQLite database for storing patient data
conn = sqlite3.connect('patient_data.db')
cursor = conn.cursor()

# Drop the existing table and recreate it with the updated schema
cursor.execute("DROP TABLE IF EXISTS vitals")
cursor.execute('''
CREATE TABLE vitals (
    timestamp TEXT,
    heart_rate INTEGER,
    blood_pressure TEXT,
    oxygen_level INTEGER,
    stress_level INTEGER,
    ecg INTEGER,
    respiration_rate INTEGER,
    status TEXT
)
''')
conn.commit()

# Insert dummy data into the database if it's empty
cursor.execute("SELECT COUNT(*) FROM vitals")
if cursor.fetchone()[0] == 0:
    dummy_data = [
        ("2024-01-01 10:00:00", 72, "120/80", 98, 25, 60, 18, "Normal"),
        ("2024-01-01 11:00:00", 110, "130/85", 88, 80, 110, 25, "High Heart Rate, Low Oxygen Level, High Stress Level"),
        ("2024-01-01 12:00:00", 95, "125/82", 92, 50, 75, 20, "Normal"),
        ("2024-01-01 13:00:00", 85, "115/75", 94, 30, 65, 19, "Normal"),
        ("2024-01-01 14:00:00", 120, "140/90", 85, 90, 130, 28, "High Heart Rate, Low Oxygen Level, High Stress Level")
    ]
    cursor.executemany("INSERT INTO vitals (timestamp, heart_rate, blood_pressure, oxygen_level, stress_level, ecg, respiration_rate, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", dummy_data)
    conn.commit()

# Authentication (Basic Login System)
users = {"doctor1": "password123", "nurse1": "password456", "123": "password789"}  # Example credentials
st.sidebar.title("Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login_successful = False
if st.sidebar.button("Login"):
    if username in users and users[username] == password:
        st.sidebar.success("Login Successful")
        login_successful = True
    else:
        st.sidebar.error("Invalid Credentials")
        st.stop()

if login_successful:
    # Function to send SMS alert via Twilio
    def send_sms_alert(message, to_phone_number="+917892796839"):
        # Replace these with your Twilio account details
        account_sid = 'AC2f0ef182c9934b71dc407460aa5cef5b'  # Replace with your Twilio Account SID
        auth_token = '7b2925d97f8aa116fbc60f7ec4351a9f'    # Replace with your Twilio Auth Token
        from_phone_number = '+13204122333'  # Replace with your Twilio phone number

        client = Client(account_sid, auth_token)

        try:
            # Create and send the SMS message
            sms = client.messages.create(
                body=message,                 # SMS content
                from_=from_phone_number,      # Twilio phone number
                to=to_phone_number            # Recipient phone number
            )
            print(f"SMS sent successfully! SID: {sms.sid}")
        except Exception as e:
            print(f"Failed to send SMS alert: {e}")

    # Simulate real-time patient data updates
    def generate_patient_data():
        return {
            "Heart Rate (bpm)": random.randint(60, 120),
            "Blood Pressure (mmHg)": f"{random.randint(100, 140)}/{random.randint(60, 90)}",
            "Oxygen Level (%)": random.randint(85, 100),
            "Stress Level (%)": random.randint(10, 100),
            "ECG (bpm)": random.randint(60, 140),
            "Respiration Rate (breaths/min)": random.randint(12, 30),
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def check_health_status(heart_rate, oxygen_level, stress_level, ecg, respiration_rate, hr_threshold, ox_threshold, stress_threshold, ecg_threshold, resp_threshold):
        anomalies = []
        if heart_rate > hr_threshold:
            anomalies.append('High Heart Rate')
        if oxygen_level < ox_threshold:
            anomalies.append('Low Oxygen Level')
        if stress_level > stress_threshold:
            anomalies.append('High Stress Level')
        if ecg > ecg_threshold:
            anomalies.append('Abnormal ECG')
        if respiration_rate > resp_threshold:
            anomalies.append('High Respiration Rate')
        return ', '.join(anomalies) if anomalies else 'Normal'

    # Streamlit Dashboard
    st.title("Real-Time Patient Monitoring Dashboard")
    st.write("Monitor and analyze patient vitals with dynamic visualizations and alerts.")

    # Sidebar for Thresholds and Refresh Rate
    st.sidebar.header("Settings")
    hr_threshold = st.sidebar.slider("Heart Rate Threshold (bpm)", 50, 150, 100)
    ox_threshold = st.sidebar.slider("Oxygen Level Threshold (%)", 80, 100, 90)
    stress_threshold = st.sidebar.slider("Stress Level Threshold (%)", 0, 100, 70)
    ecg_threshold = st.sidebar.slider("ECG Threshold (bpm)", 50, 150, 100)
    resp_threshold = st.sidebar.slider("Respiration Rate Threshold (breaths/min)", 10, 40, 25)
    refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 2)

    # Placeholder for live data
    patient_data = pd.DataFrame(columns=["Timestamp", "Heart Rate (bpm)", "Blood Pressure (mmHg)", "Oxygen Level (%)", "Stress Level (%)", "ECG (bpm)", "Respiration Rate (breaths/min)", "Status"])

    # Historical Data Viewer
    st.sidebar.header("Historical Data")
    view_history = st.sidebar.button("View Historical Data")
    if view_history:
        cursor.execute("SELECT * FROM vitals ORDER BY timestamp DESC")
        historical_data = cursor.fetchall()
        if historical_data:
            hist_df = pd.DataFrame(historical_data, columns=["Timestamp", "Heart Rate (bpm)", "Blood Pressure (mmHg)", "Oxygen Level (%)", "Stress Level (%)", "ECG (bpm)", "Respiration Rate (breaths/min)", "Status"])
            st.write("### Historical Data")
            st.dataframe(hist_df)
        else:
            st.write("No historical data available. Please generate or add new data.")

    placeholder_table = st.empty()
    placeholder_chart = st.empty()

    while True:
        # Generate new patient data
        new_data = generate_patient_data()
        heart_rate = int(new_data["Heart Rate (bpm)"])
        oxygen_level = int(new_data["Oxygen Level (%)"])
        stress_level = int(new_data["Stress Level (%)"])
        ecg = int(new_data["ECG (bpm)"])
        respiration_rate = int(new_data["Respiration Rate (breaths/min)"])
        status = check_health_status(heart_rate, oxygen_level, stress_level, ecg, respiration_rate, hr_threshold, ox_threshold, stress_threshold, ecg_threshold, resp_threshold)
        new_data["Status"] = status

        # Save data to SQLite database
        cursor.execute("INSERT INTO vitals (timestamp, heart_rate, blood_pressure, oxygen_level, stress_level, ecg, respiration_rate, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (new_data["Timestamp"], heart_rate, new_data["Blood Pressure (mmHg)"], oxygen_level, stress_level, ecg, respiration_rate, status))
        conn.commit()

        # Update DataFrame for real-time visualization
        patient_data = pd.concat([patient_data, pd.DataFrame([new_data])], ignore_index=True)
        if len(patient_data) > 50:
            patient_data = patient_data.iloc[1:]

        # Display latest metrics and alerts
        placeholder_table.dataframe(patient_data, use_container_width=True)
        if status != "Normal":
            st.error(f"ALERT: {status}")
            message = f"ALERT!\nHeart Rate: {heart_rate} bpm\nOxygen Level: {oxygen_level}%\nStress Level: {stress_level}%\nECG: {ecg} bpm\nRespiration Rate: {respiration_rate} breaths/min\nStatus: {status}"
            send_sms_alert(message)

        # Real-time visualization
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=patient_data["Timestamp"], y=patient_data["Heart Rate (bpm)"], mode="lines+markers", name="Heart Rate"))
        fig.add_trace(go.Scatter(x=patient_data["Timestamp"], y=patient_data["Oxygen Level (%)"], mode="lines+markers", name="Oxygen Level"))
        fig.add_trace(go.Scatter(x=patient_data["Timestamp"], y=patient_data["Stress Level (%)"], mode="lines+markers", name="Stress Level"))
        fig.add_trace(go.Scatter(x=patient_data["Timestamp"], y=patient_data["ECG (bpm)"], mode="lines+markers", name="ECG"))
        fig.add_trace(go.Scatter(x=patient_data["Timestamp"], y=patient_data["Respiration Rate (breaths/min)"], mode="lines+markers", name="Respiration Rate"))
        fig.update_layout(title="Patient Vitals Over Time", xaxis_title="Time", yaxis_title="Value")
        placeholder_chart.plotly_chart(fig, use_container_width=True)

        time.sleep(refresh_rate)
