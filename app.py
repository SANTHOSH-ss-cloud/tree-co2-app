import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
df = pd.read_csv("species_data.csv")
df.columns = df.columns.str.strip()

st.title("Tree CO2 Sequestration Estimator")

# User input
species = st.selectbox("Choose a Tree Species", df["common_name"])
years = st.slider("Select Time Period (years)", 1, 50, 20)
num_trees = st.number_input("Enter Number of Trees", min_value=1, value=100)

# Fetch selected tree data
tree_data = df[df["common_name"] == species].iloc[0]
growth_rate = tree_data["avg_dbh_growth"]
carbon_fraction = tree_data["carbon_fraction"]
survival_rate = tree_data["survival_rate"]

# Calculation model
def calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees=1):
    avg_dbh = growth_rate * years
    biomass_kg = 0.25 * (avg_dbh ** 2) * years
    carbon_kg = biomass_kg * carbon_fraction
    co2_kg = carbon_kg * 3.67
    total_kg = co2_kg * num_trees * survival_rate
    return total_kg / 1000  # metric tons

total_co2_tons = calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees)

st.success(f"Estimated CO2 Sequestration: {total_co2_tons:.2f} metric tons over {years} years.")

# PDF Report Generator
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Tree CO2 Sequestration Report", ln=True, align='C')

    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Species: {species}", ln=True)
    pdf.cell(200, 10, f"Years: {years}", ln=True)
    pdf.cell(200, 10, f"Number of Trees: {num_trees}", ln=True)
    pdf.cell(200, 10, f"Estimated CO2 Sequestered: {total_co2_tons:.2f} metric tons", ln=True)

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

pdf_file = generate_pdf()
st.download_button(
    label="Download Report as PDF",
    data=pdf_file,
    file_name=f"{species.replace(' ', '_')}_CO2_Report.pdf",
    mime="application/pdf"
)

# 📈 Plot 1: Carbon Captured vs Number of Trees
st.subheader("Carbon Sequestration vs Number of Trees")
tree_range = list(range(1, 1001, 50))
co2_values = [calculate_co2(growth_rate, carbon_fraction, survival_rate, years, n) for n in tree_range]

fig1, ax1 = plt.subplots()
ax1.plot(tree_range, co2_values, color='green')
ax1.set_xlabel("Number of Trees")
ax1.set_ylabel("CO2 Sequestered (metric tons)")
ax1.set_title("CO2 Sequestration vs Number of Trees")
st.pyplot(fig1)

# 📊 Plot 2: Compare Trees by CO2 Sequestration
st.subheader("Compare CO2 Sequestration Across Tree Species")

compare_data = []
for _, row in df.iterrows():
    co2 = calculate_co2(
        row["avg_dbh_growth"],
        row["carbon_fraction"],
        row["survival_rate"],
        years,
        num_trees
    )
    compare_data.append({"Species": row["common_name"], "CO2 (tons)": co2})

compare_df = pd.DataFrame(compare_data).sort_values(by="CO2 (tons)", ascending=False)

fig2, ax2 = plt.subplots(figsize=(10, 6))
sns.barplot(data=compare_df, x="CO2 (tons)", y="Species", palette="YlGn")
ax2.set_title(f"Total CO2 Sequestration Over {years} Years for {num_trees} Trees")
st.pyplot(fig2)
