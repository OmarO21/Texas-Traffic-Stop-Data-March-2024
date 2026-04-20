import streamlit as st
import plotly.express as px
from utils import load_data, load_geojson, build_county_summary

st.set_page_config(page_title="Texas Traffic Stops Dashboard", layout="wide")

st.title("Texas Traffic Stops Dashboard - March 2024")

df = load_data()
df = df[df["Region_Label"] != "Unknown"].copy()
counties_geojson = load_geojson()

# Statewide total for "% of Overall Stops"
statewide_total_stops = len(df)

# Sidebar filters
st.sidebar.header("Filters")

region_options = (
    sorted(df["Region_Label"].dropna().unique().tolist())
    if "Region_Label" in df.columns else []
)
selected_regions = st.sidebar.multiselect(
    "Region",
    region_options,
    default=region_options
)

county_options = (
    sorted(df["County"].dropna().unique().tolist())
    if "County" in df.columns else []
)
selected_counties = st.sidebar.multiselect("County", county_options)

filtered_df = df.copy()

if selected_regions:
    filtered_df = filtered_df[filtered_df["Region_Label"].isin(selected_regions)]

if selected_counties:
    filtered_df = filtered_df[filtered_df["County"].isin(selected_counties)]

# Dynamic title suffix based on selected regions
if len(selected_regions) == 1:
    title_suffix = f" - {selected_regions[0]}"
else:
    title_suffix = ""

# KPIs
total_stops = len(filtered_df)
searched_count = int(filtered_df["searched_flag"].sum())
contraband_count = int(filtered_df["contraband_flag"].sum())

search_rate = searched_count / total_stops if total_stops else 0
contraband_rate = contraband_count / total_stops if total_stops else 0

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Total Stops", f"{total_stops:,}")
c2.metric("Searches", f"{searched_count:,}")
c3.metric("Contraband Found", f"{contraband_count:,}")
c4.metric("Search Rate", f"{search_rate:.2%}")
c5.metric("Contraband Rate", f"{contraband_rate:.2%}")

st.divider()

county_summary = build_county_summary(filtered_df)

# Add % of statewide stops
county_summary["pct_overall_stops"] = (
    county_summary["total_stops"] / statewide_total_stops
    if statewide_total_stops else 0
)

# County map
st.subheader(f"Texas County Map{title_suffix}")

map_options = {
    "Total Stops": "total_stops",
    "Searches": "searched_count",
    "Contraband Found": "contraband_count",
    "Search Rate": "search_rate",
    "Contraband Rate": "contraband_rate"
}

selected_map_label = st.selectbox(
    "Color map by",
    list(map_options.keys())
)
 
map_metric = map_options[selected_map_label]

fig_map = px.choropleth(
    county_summary,
    geojson=counties_geojson,
    locations="County",
    featureidkey="properties.CNTY_NM",
    color=map_metric,
    color_continuous_scale="Blues",
    hover_name="County",
    hover_data={
        "total_stops": ":,",
        "searched_count": ":,",
        "contraband_count": ":,",
        "search_rate": ":.2%",
        "contraband_rate": ":.2%",
        "pct_overall_stops": ":.2%"
    },
    labels={
        "County": "County",
        "total_stops": "Total Stops",
        "searched_count": "Searches",
        "contraband_count": "Contraband Found",
        "search_rate": "Search Rate",
        "contraband_rate": "Contraband Rate",
        "pct_overall_stops": "% of Overall Stops"
    }
)

fig_map.update_geos(
    fitbounds="locations",
    visible=False,
    bgcolor="rgba(0,0,0,0)"
)

fig_map.update_layout(
    height=620,
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig_map, use_container_width=True)

st.divider()

row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

# Chart 1: Top Counties
with row1_col1:
    st.subheader(f"Top Counties{title_suffix}")

    bar_options = {
        "Total Stops": "total_stops",
        "Searches": "searched_count",
        "Contraband Found": "contraband_count",
        "Search Rate": "search_rate",
        "Contraband Rate": "contraband_rate"
    }

    selected_bar_label = st.selectbox(
        "County metric",
        list(bar_options.keys()),
        key="bar_metric"
    )

    bar_metric = bar_options[selected_bar_label]

    top_counties = county_summary.sort_values(bar_metric, ascending=False).head(10)

    fig_bar = px.bar(
        top_counties,
        x="County",
        y=bar_metric,
        title=f"Top 10 Counties{title_suffix} — {selected_bar_label}",
        labels={
            "County": "County",
            "total_stops": "Total Stops",
            "searched_count": "Searches",
            "contraband_count": "Contraband Found",
            "search_rate": "Search Rate",
            "contraband_rate": "Contraband Rate"
        }
    )

    if "Rate" in selected_bar_label:
        fig_bar.update_yaxes(tickformat=".0%")

    fig_bar.update_layout(height=400, margin=dict(l=0, r=0, t=50, b=0))
    st.plotly_chart(fig_bar, use_container_width=True)

# Chart 2: Stops by Day of Week
with row1_col2:
    st.subheader(f"Stops by Day of Week{title_suffix}")

    if "Datetime" in filtered_df.columns:
        day_order = [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]

        day_summary = filtered_df.copy()
        day_summary["Day of Week"] = day_summary["Datetime"].dt.day_name()

        day_summary = (
            day_summary["Day of Week"]
            .dropna()
            .value_counts()
            .reindex(day_order, fill_value=0)
            .reset_index()
        )
        day_summary.columns = ["Day of Week", "Count"]

        fig_day = px.bar(
            day_summary,
            x="Day of Week",
            y="Count",
            title=f"Traffic Stops by Day of Week{title_suffix}",
            labels={"Day of Week": "Day of Week", "Count": "Stops"}
        )

        fig_day.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=50, b=0)
        )

        st.plotly_chart(fig_day, use_container_width=True)

# Chart 3: Stops by Driver Race/Sex
with row2_col1:
    st.subheader(f"Stops by Driver Race/Sex{title_suffix}")

    if "Driver_Race_Sex" in filtered_df.columns:
        race_sex_summary = (
            filtered_df["Driver_Race_Sex"]
            .fillna("Unknown")
            .value_counts()
            .head(10)
            .reset_index()
        )
        race_sex_summary.columns = ["Driver Race/Sex", "Count"]

        fig_race_sex = px.pie(
            race_sex_summary,
            names="Driver Race/Sex",
            values="Count",
            title=f"Driver Race/Sex Distribution{title_suffix}",
            hole=0.45
        )

        fig_race_sex.update_traces(
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>Stops: %{value:,}<br>Percent: %{percent}<extra></extra>"
        )

        fig_race_sex.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=50, b=0),
            legend_title="Driver Race/Sex",
            legend=dict(
                orientation="v",
                y=0.5,
                yanchor="middle",
                x=1.02,
                xanchor="left"
            )
        )

        st.plotly_chart(fig_race_sex, use_container_width=True)

# Chart 4: Stops by Hour
with row2_col2:
    st.subheader(f"Stops by Hour{title_suffix}")

    if "Hour" in filtered_df.columns:
        hour_summary = (
            filtered_df["Hour"]
            .dropna()
            .value_counts()
            .sort_index()
            .reset_index()
        )
        hour_summary.columns = ["Hour", "Count"]

        fig_hour = px.line(
            hour_summary,
            x="Hour",
            y="Count",
            title=f"Traffic Stops by Hour of Day{title_suffix}",
            labels={"Hour": "Hour of Day", "Count": "Stops"},
            markers=True
        )

        fig_hour.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=50, b=0)
        )

        st.plotly_chart(fig_hour, use_container_width=True)

# County summary table
st.subheader(f"County Summary{title_suffix}")

county_summary_display = county_summary.rename(
    columns={
        "County": "County",
        "total_stops": "Total Stops",
        "searched_count": "Searches",
        "contraband_count": "Contraband Found",
        "search_rate": "Search Rate",
        "contraband_rate": "Contraband Rate",
        "pct_overall_stops": "% of Overall Stops"
    }
)

st.dataframe(
    county_summary_display
    .sort_values("Total Stops", ascending=False)
    .reset_index(drop=True)
    .style
    .hide(axis="index")
    .format({
        "Total Stops": "{:,}",
        "Searches": "{:,}",
        "Contraband Found": "{:,}",
        "Search Rate": "{:.2%}",
        "Contraband Rate": "{:.2%}",
        "% of Overall Stops": "{:.2%}"
    }),
    use_container_width=True
)

## https://texas-traffic-stops-march-2024.streamlit.app/
## streamlit run app.py

