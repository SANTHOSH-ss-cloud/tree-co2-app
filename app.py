import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import os

# Load cleaned dataset
df = pd.read_csv("filtered_india_tree_data.csv")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

st.title("🌳 Tree CO₂ Sequestration Comparator")

# User Inputs
city = st.selectbox("Select Your City", sorted(df["city"].dropna().unique()))
user_tree_name = st.text_input("Give a Nickname for Your Tree 🌱", "My Green Tree")
user_species = st.selectbox("Choose a Tree Species", sorted(df["common_name"].dropna().unique()))
years = st.slider("Select Number of Years", 1, 50, 20)
num_trees = st.number_input("Number of Trees", min_value=1, value=10)

# Get user-selected tree data
user_data = df[df["common_name"] == user_species].iloc[0]

def calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees):
    dbh = growth_rate * years
    biomass = 0.25 * (dbh ** 2) * years
    carbon = biomass * carbon_fraction
    co2 = carbon * 3.67
    return (co2 * survival_rate * num_trees) / 1000  # in metric tons

user_co2 = calculate_co2(
    user_data["avg_dbh_growth"], user_data["carbon_fraction"], user_data["survival_rate"], years, num_trees
)

st.success(f"🌱 Estimated CO₂ for {user_species}: **{user_co2:.2f} metric tons** over {years} years.")

# AI Suggestion: Find best tree in city with higher CO2 than user tree
ai_df = df[(df["city"] == city) & (df["common_name"] != user_species)].dropna(subset=["avg_dbh_growth", "carbon_fraction", "survival_rate"])
ai_df["estimated_co2"] = ai_df.apply(lambda row: calculate_co2(
    row["avg_dbh_growth"], row["carbon_fraction"], row["survival_rate"], years, num_trees
), axis=1)

ai_df = ai_df[ai_df["estimated_co2"] > user_co2]

if not ai_df.empty:
    ai_species = ai_df.sort_values(by="estimated_co2", ascending=False).iloc[0]
    ai_co2 = ai_species["estimated_co2"]
    st.info(f"🤖 AI Suggests: {ai_species['common_name']} ({ai_species['scientific_name']})")
    st.success(f"🤖 Estimated CO₂: **{ai_co2:.2f} metric tons**")
else:
    ai_species = None
    ai_co2 = 0
    st.warning("🤖 No better species found by AI for this city.")

# Bar Chart Comparison
def plot_chart(user_co2, ai_co2):
    fig, ax = plt.subplots()
    ax.bar(["User Tree", "AI Tree"], [user_co2, ai_co2], color=["green", "blue"])
    ax.set_ylabel("CO2 Sequestered (metric tons)")
    ax.set_title("User vs AI Tree CO2 Comparison")
    buffer = BytesIO()
    fig.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close(fig)
    return buffer

chart_img = plot_chart(user_co2, ai_co2)
st.image(chart_img, caption="User vs AI Tree CO₂", use_container_width=True)

# PDF Report Generator (no emojis or Unicode)
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Tree CO2 Comparison Report", ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(190, 10, f"City: {city}", ln=True)
    pdf.cell(190, 10, f"User Tree: {user_species} (Nickname: {user_tree_name})", ln=True)
    pdf.cell(190, 10, f"Estimated CO2: {user_co2:.2f} metric tons", ln=True)

    if ai_species is not None:
        pdf.cell(190, 10, f"AI Suggested Tree: {ai_species['common_name']}", ln=True)
        pdf.cell(190, 10, f"Estimated CO2: {ai_co2:.2f} metric tons", ln=True)
    else:
        pdf.cell(190, 10, f"No better AI suggestion available for this city.", ln=True)

    image_path = "/tmp/temp_chart.png"
    with open(image_path, "wb") as f:
        f.write(chart_img.getbuffer())
    pdf.image(image_path, x=10, w=180)
    os.remove(image_path)

    out_buffer = BytesIO()
    out_buffer.write(pdf.output(dest='S').encode('latin1'))  # Ensures no Unicode errors
    out_buffer.seek(0)
    return out_buffer

# Download Button
pdf_data = generate_pdf()
st.download_button("📄 Download Comparison Report", data=pdf_data, file_name="tree_comparison_report.pdf", mime="application/pdf")
