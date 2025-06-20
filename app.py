import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import os
import tempfile

try:
    # Load dataset
    df = pd.read_csv("strict_filtered_species_data.csv")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Required columns check
    required_cols = ["common_name", "avg_dbh_growth", "carbon_fraction", "survival_rate"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            st.stop()

    df = df.dropna(subset=required_cols)
    indian_tree_species = sorted(df["common_name"].dropna().unique())

    if not indian_tree_species:
        st.error("No valid tree species found in the dataset.")
        st.stop()

    indian_cities = [
        "Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Pune", "Jaipur", "Lucknow",
        "Kanpur", "Nagpur", "Indore", "Bhopal", "Patna", "Vadodara", "Ludhiana", "Agra", "Nashik", "Faridabad",
        "Meerut", "Rajkot", "Kalyan", "Vasai", "Varanasi", "Srinagar", "Ranchi", "Amritsar", "Jodhpur", "Coimbatore"
    ]

    # UI
    st.title("Tree CO2 Sequestration Comparator (India)")

    city = st.selectbox("Select Your City (India Only)", indian_cities)
    species = st.selectbox("Choose a Tree Species (India Only)", indian_tree_species)
    nickname = st.text_input("Give a Nickname to Your Tree", "My Tree")
    years = st.slider("Years to Estimate CO2", 1, 50, 20)
    num_trees = st.number_input("Number of Trees", min_value=1, value=10)

    # Fetch selected species data
    tree_data = df[df["common_name"] == species]
    if tree_data.empty:
        st.error("Selected tree species not found in dataset.")
        st.stop()
    tree_data = tree_data.iloc[0]

    # CO2 calculation
    def calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees):
        dbh = max(0, growth_rate * years)
        biomass = 0.25 * (dbh ** 2) * years
        carbon = biomass * carbon_fraction
        co2 = carbon * 3.67
        return (co2 * survival_rate * num_trees) / 1000

    user_co2 = calculate_co2(tree_data["avg_dbh_growth"], tree_data["carbon_fraction"], tree_data["survival_rate"], years, num_trees)
    st.success(f"Your Tree ({species}) will sequester: {user_co2:.2f} metric tons of CO2 in {years} years.")

    # AI Recommendation
    ai_df = df[df["common_name"] != species].copy()
    ai_df["estimated_co2"] = ai_df.apply(lambda row: calculate_co2(
        row["avg_dbh_growth"], row["carbon_fraction"], row["survival_rate"], years, num_trees), axis=1)

    better_ai = ai_df[ai_df["estimated_co2"] > user_co2]

    if better_ai.shape[0] == 0:
        ai_species = None
        ai_co2 = 0
        st.warning("No better tree found by AI.")
    else:
        sorted_ai = better_ai.sort_values("estimated_co2", ascending=False)
        if sorted_ai.shape[0] >= 1:
            ai_best = sorted_ai.iloc[0]
            ai_species = ai_best["common_name"]
            ai_co2 = ai_best["estimated_co2"]
            st.info(f"AI Suggests: {ai_species}")
            st.success(f"AI Tree CO2 Estimate: {ai_co2:.2f} metric tons")
        else:
            ai_species = None
            ai_co2 = 0
            st.warning("AI recommendation failed to return any result.")

    # Chart
    def generate_chart(user_co2, ai_co2):
        fig, ax = plt.subplots()
        ax.bar(["Your Tree", "AI Tree"], [user_co2, ai_co2], color=["green", "blue"])
        ax.set_ylabel("CO2 Sequestered (metric tons)")
        ax.set_title("User vs AI Tree CO2 Comparison")
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        return buf

    chart_img = generate_chart(user_co2, ai_co2)
    st.image(chart_img, caption="User vs AI Tree CO2", use_container_width=True)

    # PDF Report using only safe fonts
    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, "Tree CO2 Comparison Report", ln=True, align='C')
        pdf.set_font("Arial", "", 12)
        pdf.ln(10)
        pdf.cell(190, 10, f"City: {city}", ln=True)
        pdf.cell(190, 10, f"Your Tree: {species} (Nickname: {nickname})", ln=True)
        pdf.cell(190, 10, f"Years: {years}", ln=True)
        pdf.cell(190, 10, f"Number of Trees: {num_trees}", ln=True)
        pdf.cell(190, 10, f"Estimated CO2: {user_co2:.2f} metric tons", ln=True)
        if ai_species:
            pdf.cell(190, 10, f"AI Tree: {ai_species}", ln=True)
            pdf.cell(190, 10, f"AI CO2 Estimate: {ai_co2:.2f} metric tons", ln=True)
        else:
            pdf.cell(190, 10, "No better tree recommended by AI.", ln=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(chart_img.getbuffer())
            image_path = tmp_file.name
        try:
            pdf.image(image_path, x=10, w=180)
        finally:
            os.remove(image_path)

        output = BytesIO()
        output.write(pdf.output(dest="S"))
        output.seek(0)
        return output

    pdf_bytes = generate_pdf()
    st.download_button("Download Report as PDF", data=pdf_bytes, file_name="tree_comparison.pdf", mime="application/pdf")

except FileNotFoundError:
    st.error("Error: 'strict_filtered_species_data.csv' not found.")
except Exception as e:
    st.error(f"An unexpected error occurred: {e}. Please check your code and data.")
