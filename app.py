import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import matplotlib.pyplot as plt

# Load species dataset
df = pd.read_csv("species_data.csv")
df.columns = df.columns.str.strip()

st.title("🌳 Tree CO₂ Sequestration Estimator")

# User Inputs
species = st.selectbox("Choose a Tree Species", df["common_name"])
years = st.slider("Select Time Period (years)", 1, 50, 20)
num_trees = st.number_input("Enter Number of Trees", min_value=1, value=100)

# Retrieve selected species data
tree_data = df[df["common_name"] == species].iloc[0]
growth_rate = tree_data["avg_dbh_growth"]
carbon_fraction = tree_data["carbon_fraction"]
survival_rate = tree_data["survival_rate"]

# CO₂ Calculation Function
def calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees=1):
    avg_dbh = growth_rate * years
    biomass_kg = 0.25 * (avg_dbh ** 2) * years
    carbon_kg = biomass_kg * carbon_fraction
    co2_kg = carbon_kg * 3.67
    total_kg = co2_kg * num_trees * survival_rate
    return total_kg / 1000  # metric tons

# Estimate CO₂
total_co2_tons = calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees)

st.success(f"🌱 Estimated CO₂ Sequestration: {total_co2_tons:.2f} metric tons over {years} years.")

# PDF Report Generator
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Tree CO₂ Sequestration Report", ln=True, align='C')
    
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Species: {species}", ln=True)
    pdf.cell(200, 10, f"Years: {years}", ln=True)
    pdf.cell(200, 10, f"Number of Trees: {num_trees}", ln=True)
    pdf.cell(200, 10, f"Estimated CO₂ Sequestered: {total_co2_tons:.2f} metric tons", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, "Model Details:", ln=True)
    pdf.cell(200, 10, f"- Avg. DBH Growth: {growth_rate} cm/year", ln=True)
    pdf.cell(200, 10, f"- Carbon Fraction: {carbon_fraction}", ln=True)
    pdf.cell(200, 10, f"- Survival Rate: {survival_rate}", ln=True)

    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output

# PDF Download Button
pdf_file = generate_pdf()
st.download_button(
    label="📄 Download Report as PDF",
    data=pdf_file,
    file_name=f"{species.replace(' ', '_')}_CO2_Report.pdf",
    mime="application/pdf"
)

# 📈 Show Graph: CO2 Sequestered vs Number of Trees
st.subheader(f"📈 CO₂ Sequestered vs Number of Trees for {species} over {years} years")

x_vals = list(range(1, 1001, 50))
y_vals = [calculate_co2(growth_rate, carbon_fraction, survival_rate, years, n) for n in x_vals]

fig, ax = plt.subplots()
ax.plot(x_vals, y_vals, marker='o', color='forestgreen')
ax.set_xlabel("Number of Trees")
ax.set_ylabel("CO₂ Sequestered (metric tons)")
ax.set_title(f"{species} - CO₂ Sequestration over {years} years")
ax.grid(True)

st.pyplot(fig)
