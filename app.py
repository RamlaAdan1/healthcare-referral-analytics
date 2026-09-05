import altair as alt
import duckdb
import streamlit as st

from data_pipeline import DATABASE_FILE, build_data_pipeline


st.set_page_config(
    page_title="AIRTOS Referral Data Platform",
    layout="wide"
)


@st.cache_data
def load_kpis():
    build_data_pipeline()

    with duckdb.connect(
        str(DATABASE_FILE),
        read_only=True
    ) as connection:

        return connection.execute("""
            SELECT
                metric,
                category,
                as_is,
                to_be,
                unit,
                percentage_change
            FROM referral_kpis
        """).df()


def get_kpi(data, metric_name):
    matching_rows = data[
        data["metric"] == metric_name
    ]

    if matching_rows.empty:
        st.error(
            f"Required KPI was not found: {metric_name}"
        )
        st.stop()

    return matching_rows.iloc[0]


def create_comparison_chart(
    data,
    label_column,
    value_column,
    label_order,
    height
):
    long_data = data.melt(
        id_vars=label_column,
        value_vars=["AS-IS", "TO-BE"],
        var_name="Scenario",
        value_name=value_column
    )

    base_chart = alt.Chart(long_data).encode(
        y=alt.Y(
            label_column,
            type="nominal",
            title=None,
            sort=label_order,
            axis=alt.Axis(
                labelLimit=300,
                labelFontSize=13
            )
        ),
        yOffset=alt.YOffset("Scenario:N"),
        x=alt.X(
            value_column,
            type="quantitative",
            title=value_column
        )
    )

    bars = base_chart.mark_bar(
        cornerRadiusEnd=4
    ).encode(
        color=alt.Color(
            "Scenario:N",
            scale=alt.Scale(
                domain=["AS-IS", "TO-BE"],
                range=["#EF4444", "#10B981"]
            ),
            legend=alt.Legend(
                title=None,
                orient="bottom"
            )
        ),
        tooltip=[
            alt.Tooltip(
                label_column,
                type="nominal",
                title=label_column
            ),
            alt.Tooltip(
                "Scenario:N",
                title="Scenario"
            ),
            alt.Tooltip(
                value_column,
                type="quantitative",
                title=value_column,
                format=".2f"
            )
        ]
    )

    numbers = base_chart.mark_text(
        align="right",
        baseline="middle",
        dx=-6,
        color="white",
        fontSize=12,
        fontWeight="bold"
    ).encode(
        text=alt.Text(
            value_column,
            type="quantitative",
            format=".2f"
        )
    )

    return (
        bars + numbers
    ).properties(
        height=height
    )


# Load the processed data

kpi_data = load_kpis()

completed = get_kpi(
    kpi_data,
    "Cases completed at Level 5"
)

referrals = get_kpi(
    kpi_data,
    "Onward referrals to Level 6"
)

ward_wait = get_kpi(
    kpi_data,
    "Ward review queue"
)

reception_wait = get_kpi(
    kpi_data,
    "Reception queue"
)


# Dashboard heading

st.title("AIRTOS Referral Data Platform")

st.caption(
    "Analytics for Kenya's Level 4–6 public hospital referral pathway "
    "· Simulated and anonymised academic data only"
)


# Main KPI results

st.subheader("Expected TO-BE Outcomes")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Cases completed at Level 5",
    value=f"{completed['to_be']:.1f} per day",
    delta=f"{completed['percentage_change']:+.1f}%"
)

col2.metric(
    label="Onward referrals",
    value=f"{referrals['to_be']:.1f} per day",
    delta=f"{referrals['percentage_change']:+.1f}%",
    delta_color="inverse"
)

col3.metric(
    label="Ward review waiting time",
    value=f"{ward_wait['to_be']:.1f} minutes",
    delta=f"{ward_wait['percentage_change']:+.1f}%",
    delta_color="inverse"
)

col4.metric(
    label="Reception waiting time",
    value=f"{reception_wait['to_be']:.1f} minutes",
    delta=f"{reception_wait['percentage_change']:+.1f}%",
    delta_color="inverse"
)

st.caption(
    "Green changes show an improvement compared with "
    "the current AS-IS process."
)


# Prepare waiting-time data

waiting_data = (
    kpi_data[
        kpi_data["category"] == "Waiting time"
    ][["metric", "as_is", "to_be"]]
    .rename(columns={
        "metric": "Referral stage",
        "as_is": "AS-IS",
        "to_be": "TO-BE"
    })
)

waiting_data["Referral stage"] = waiting_data[
    "Referral stage"
].replace({
    "Ward review queue": "Ward review",
    "Speciality availability queue": "Speciality availability",
    "External transport request queue": "External transport request",
    "Transport coordination queue": "Transport coordination",
    "Reception queue": "Reception"
})

waiting_order = [
    "Ward review",
    "Speciality availability",
    "External transport request",
    "Transport coordination",
    "Reception"
]


# Prepare patient-flow data

flow_data = (
    kpi_data[
        kpi_data["category"] == "Patient flow"
    ][["metric", "as_is", "to_be"]]
    .rename(columns={
        "metric": "Measure",
        "as_is": "AS-IS",
        "to_be": "TO-BE"
    })
)

flow_data["Measure"] = flow_data["Measure"].replace({
    "Cases completed at Level 5": "Completed at Level 5",
    "Onward referrals to Level 6": "Referred to Level 6"
})

flow_order = [
    "Completed at Level 5",
    "Referred to Level 6"
]


# Comparison charts

st.divider()

st.subheader("AS-IS and TO-BE Comparison")

waiting_tab, flow_tab = st.tabs([
    "Waiting Times",
    "Patient Flow"
])


with waiting_tab:
    waiting_chart = create_comparison_chart(
        data=waiting_data,
        label_column="Referral stage",
        value_column="Minutes",
        label_order=waiting_order,
        height=360
    )

    st.altair_chart(
        waiting_chart,
        width="stretch"
    )

    st.caption(
        "The TO-BE process reduces waiting time "
        "across all five referral stages."
    )


with flow_tab:
    flow_chart = create_comparison_chart(
        data=flow_data,
        label_column="Measure",
        value_column="Average cases per day",
        label_order=flow_order,
        height=240
    )

    st.altair_chart(
        flow_chart,
        width="stretch"
    )

    st.caption(
        "The TO-BE process completes more cases at Level 5 "
        "and sends fewer referrals to Level 6."
    )


# Technical information

st.divider()

with st.expander(
    "Technical details and data download",
    expanded=False
):
    st.markdown("**Data pipeline**")

    st.write(
        "CSV → Python → DuckDB → SQL → Streamlit"
    )

    st.caption(
        "The source data is transformed with Python, stored "
        "in DuckDB, queried with SQL and displayed in Streamlit."
    )

    st.markdown("**Processed KPI table**")

    display_table = kpi_data.rename(columns={
        "metric": "Metric",
        "category": "Category",
        "as_is": "AS-IS",
        "to_be": "TO-BE",
        "unit": "Unit",
        "percentage_change": "Change (%)"
    })

    st.dataframe(
        display_table,
        hide_index=True,
        width="stretch"
    )

    csv_data = display_table.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download processed data (CSV)",
        data=csv_data,
        file_name="airtos_referral_kpis.csv",
        mime="text/csv"
    )

    st.markdown("**Data quality**")

    total_rows = len(kpi_data)
    missing_values = int(
        kpi_data.isna().sum().sum()
    )
    duplicate_metrics = int(
        kpi_data.duplicated(
            subset=["metric"]
        ).sum()
    )

    quality1, quality2, quality3 = st.columns(3)

    quality1.metric(
        "KPI rows",
        total_rows
    )

    quality2.metric(
        "Missing values",
        missing_values
    )

    quality3.metric(
        "Duplicate metrics",
        duplicate_metrics
    )

    if missing_values == 0 and duplicate_metrics == 0:
        st.success(
            "All data quality checks passed."
        )
    else:
        st.warning(
            "The KPI table contains data quality issues."
        )
