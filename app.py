import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load species data
df = pd.read_csv("species_data.csv")

# UI Inputs
st.title("🌳 Tree CO₂ Sequestration Estimator")
st.write("Estimate long-term CO₂ capture by tree plantations.")

species = st.selectbox("Choose a Tree Species", df["species"])
num_trees = st.number_input("Number of Trees", min_value=100, max_value=10000, value=1000)
years = st.slider("Years to Simulate", min_value=5, max_value=30, value=20)

# Get selected species parameters
tree = df[df["species"] == species].iloc[0]
growth_rate = tree["avg_growth_rate_dbh"]
carbon_frac = tree["carbon_fraction"]
survival_rate = tree["survival_rate"]

def simulate_co2(years, trees, growth_rate, carbon_frac, survival_rate):
    yearly_co2 = []
    survival = 1
    for year in range(1, years + 1):
        dbh = growth_rate * year
        agb = 0.25 * (dbh ** 2.46)  # Biomass formula
        co2 = agb * carbon_frac * 3.67
        survival *= survival_rate
        yearly_co2.append(co2 * trees * survival)
    return yearly_co2

# Run Simulation
co2_data = simulate_co2(years, num_trees, growth_rate, carbon_frac, survival_rate)

# Plot
st.subheader("CO₂ Sequestered Over Time (kg)")
fig, ax = plt.subplots()
ax.plot(range(1, years + 1), co2_data, marker='o')
ax.set_xlabel("Year")
ax.set_ylabel("CO₂ (kg)")
st.pyplot(fig)

# Summary
st.subheader("Summary")
st.write(f"Total CO₂ captured after {years} years: **{sum(co2_data):,.2f} kg**")
