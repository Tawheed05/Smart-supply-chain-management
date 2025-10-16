import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import matplotlib.pyplot as plt



# -------------------------------
# Backend URL
# -------------------------------
BACKEND_URL = "http://127.0.0.1:8000"

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="Hacktrix'25 Logistics & Supply Chain",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Custom CSS for Dark Theme & Styling
# -------------------------------
st.markdown("""
<style>
/* Body background */
[data-testid="stAppViewContainer"] { background-color: #121212; color: white; }
/* Sidebar background */
[data-testid="stSidebar"] { background-color: #0d1b2a; color: white; }
/* Headers */
h1, h2, h3, h4 { color: #0f4c75; }
/* Metric cards */
.css-1lcbmhc.e1fqkh3o3 { background-color: #3282b8 !important; color: white !important; border-radius: 10px !important; }
.css-1lcbmhc.e1fqkh3o3:hover { transform: scale(1.05); transition: 0.2s; }
/* Buttons */
.stButton>button { background-color: #0f4c75; color: white; border-radius: 10px; padding: 0.6em 1.2em; font-weight: bold; }
/* Inputs */
.stTextInput>div>input, .stNumberInput>div>input, .stTextArea>div>textarea { background-color: #1b263b; color: white; border-radius: 5px; padding: 0.5em; }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Sidebar
# -------------------------------
st.sidebar.title("Hacktrix'25 Dashboard")
st.sidebar.markdown("""
**Features:**
- AI Demand Prediction
- Route Optimization
- Interactive Maps & Graphs
- Metrics & Analytics
""")

# -------------------------------
# Tabs
# -------------------------------
tab1, tab2 = st.tabs(["📈 Demand Prediction", "🚚 Route Optimization"])

# -------------------------------
# Demand Prediction
# -------------------------------
with tab1:
    st.header("Demand Forecast")
    st.markdown("Provide historical daily demand (min 14 days)")

    uploaded_file = st.file_uploader("Upload CSV (1 column: daily demand)", type=["csv"])
    if uploaded_file:
        data = pd.read_csv(uploaded_file, header=None)
        historical_demand = data[0].tolist()
    else:
        historical_demand = st.text_input(
            "Or enter comma-separated daily demand:",
            value="50,52,49,55,60,58,62,65,63,70,72,68,75,80"
        )
        historical_demand = [int(x.strip()) for x in historical_demand.split(",") if x.strip()]

    days_ahead = st.number_input("Days to predict ahead:", min_value=1, max_value=30, value=7)

    product_category = st.selectbox(
    "Select Product Category",
    ["Medicines", "Food", "Electronics", "Clothes", "Others"]
)


    if st.button("Predict Demand"):
        if len(historical_demand) < 14:
            st.warning("Please provide at least 14 days of history!")
        else:
            payload = {
    "history": historical_demand,
    "days_ahead": int(days_ahead),
    "product_category": product_category
}

            try:
                response = requests.post(f"{BACKEND_URL}/predict/demand", json=payload)
                response.raise_for_status()
                pred = response.json()["prediction"]

                # Metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Predicted Demand", f"{sum(pred)}")
                col2.metric("Max Demand", f"{max(pred)}")
                col3.metric("Min Demand", f"{min(pred)}")

                # Plot
                fig, ax = plt.subplots(figsize=(10,4))
                ax.plot(range(len(historical_demand)), historical_demand, marker='o', label='History', color="#0f4c75")
                ax.plot(range(len(historical_demand), len(historical_demand)+len(pred)), pred, marker='o', linestyle='--', color="#3282b8", label='Predicted')
                ax.set_facecolor('#121212')
                ax.set_xlabel("Days", color="white")
                ax.set_ylabel("Demand", color="white")
                ax.set_title("Historical vs Predicted Demand", color="white")
                ax.legend()
                ax.tick_params(colors='white')
                st.pyplot(fig)

            except requests.exceptions.HTTPError as err:
                st.error(f"Backend returned error: {err}")
                st.write(response.text)
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")

# -------------------------------
# Route Optimization
# -------------------------------
with tab2:
    st.header("Route Optimization")
    st.markdown("Upload depot & stops CSV or enter manually.")

    depot_lat = st.number_input("Depot Latitude", value=12.97, format="%.6f")
    depot_lon = st.number_input("Depot Longitude", value=77.59, format="%.6f")

    # -------------------------------
    # Product Category & Vehicle Type
    # -------------------------------
    product_category = st.selectbox(
        "Product Category",
        options=["General", "Medical", "Food", "Electronics", "Other"]
    )

    vehicle_type = st.selectbox(
        "Vehicle Type",
        options=["Bike", "Van", "Truck", "Electric Van"]
    )

    # Emission factors (kg CO2 per km)
    emission_factors = {
        "Bike": 0.05,
        "Van": 0.12,
        "Truck": 0.3,
        "Electric Van": 0.0
    }

    # -------------------------------
    # Traffic & Disaster Mode Options
    # -------------------------------
    traffic_aware = st.checkbox("Optimize considering traffic", value=False)
    disaster_mode = st.checkbox("Emergency / Disaster Delivery", value=False)



    stops_file = st.file_uploader("Upload stops CSV (id,lat,lon)", type=["csv"])
    if stops_file:
        stops_df = pd.read_csv(stops_file)
    else:
        stops_text = st.text_area(
            "Or enter stops CSV manually (id,lat,lon per line)",
            value="A,12.9,77.6\nB,12.95,77.55\nC,12.98,77.6"
        )
        lines = [x.strip() for x in stops_text.split("\n") if x.strip()]
        stops = [line.split(",") for line in lines]
        stops_df = pd.DataFrame(stops, columns=["id","lat","lon"])
        stops_df["lat"] = stops_df["lat"].astype(float)
        stops_df["lon"] = stops_df["lon"].astype(float)
        stops_df["id"] = stops_df["id"].astype(str)

    if st.button("Optimize Route"):
        stops_list = stops_df.to_dict(orient="records")

        payload = {
            "depot": {"id": "Depot", "lat": float(depot_lat), "lon": float(depot_lon)},
            "stops": stops_list

        }

        payload["vehicle_type"] = vehicle_type
        payload["product_category"] = product_category
        payload["traffic_aware"] = traffic_aware
        payload["disaster_mode"] = disaster_mode


        st.subheader("Payload Preview")
        st.json(payload)

        try:
            response = requests.post(f"{BACKEND_URL}/optimize/route", json=payload)
            response.raise_for_status()
            route_result = response.json()

            # -------------------------------
            # CO2 Emission Calculation
            # -------------------------------
            vehicle_emission_factor = emission_factors.get(vehicle_type, 0.1)
            total_co2 = route_result['distance'] * vehicle_emission_factor


            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Stops", f"{len(stops_df)}")
            col2.metric("Total Distance (km)", f"{route_result['distance']:.2f}")
            col3.metric("Estimated CO₂ Emission (kg)", f"{total_co2:.2f}")
            col4.metric("Vehicle", vehicle_type)


            # Route display
            st.success("Optimized Route:")
            st.write("Depot → " + " → ".join(route_result["route"][1:-1]) + " → Depot")

            # Map visualization
            # ----------------
            # CORRECTED CODE ✅
            # ----------------
            # Get the coordinate data as before
            route_coords_list = route_result.get("route_coords", [])

            for idx, stop in enumerate(route_coords_list):
                stop["label"] = str(idx) if stop["id"] != "Depot" else "Depot"

            # Convert the data for both layers into PANDAS DATAFRAMES
            scatterplot_data = pd.DataFrame(route_coords_list)
            path_data = pd.DataFrame([{"path": [[c["lon"], c["lat"]] for c in route_coords_list]}])

            st.pydeck_chart(
                pdk.Deck(
                    map_style="mapbox://styles/mapbox/dark-v10",
                    initial_view_state=pdk.ViewState(
                        latitude=float(depot_lat),
                        longitude=float(depot_lon),
                        zoom=11
                    ),
                    layers=[
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=scatterplot_data, # Use the DataFrame
                            get_position="[lon, lat]",
                            get_color=[255, 165, 0],
                            get_radius=120,
                            pickable=True,
                            auto_highlight=True,
                            
                        ),
                        pdk.Layer(
                            "PathLayer",
                            data=path_data, # Use the DataFrame
                            get_color=[0, 255, 255],
                            get_width=5
                        )
                    ],
                    tooltip={"text": "{label}"}
                )
            )


        except requests.exceptions.HTTPError as err:
            st.error(f"Backend returned error: {err}")
            st.write(response.text)
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")
