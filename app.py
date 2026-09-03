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


def get_kpi(metric_name):
    return kpi_data[
        kpi_data["metric"] == metric_name
    ].iloc[0]


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
                labelLimit=350,
                labelFontSize=14
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
            alt.Tooltip(label_column, type="nominal"),
            alt.Tooltip("Scenario:N", title="Scenario"),
            alt.Tooltip(
                value_column,
                type="quantitative",
                format=".2f"
            )
        ]
    )

    numbers = base_chart.mark_text(
        align="right",
        baseline="middle",
        dx=-6,
        color="white",
        fontSize=13,
        fontWeight="bold"
    ).encode(
        text=alt.Text(
            value_column,
            type="quantitative",
            format=".2f"
        )
    )

    return (bars + numbers).properties(height=height)


kpi_data = load_kpis()

completed = get_kpi("Cases completed at Level 5")
referrals = get_kpi("Onward referrals to Level 6")
ward_wait = get_kpi("Ward review queue")
reception_wait = get_kpi("Reception queue")


st.title("AIRTOS: Healthcare Referral Data Platform")

st.caption(
    "Data pipeline and analytics for Kenya's "
    "Level 4–6 public hospital referral pathway"
)

st.info(
    "This dashboard uses simulated and anonymised academic data. "
    "It does not contain real patient records."
)


# KPI cards

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Cases completed at Level 5",
    f"{completed['to_be']:.2f} per day",
    f"{completed['percentage_change']:+.2f}%"
)

col2.metric(
    "Onward referrals",
    f"{referrals['to_be']:.2f} per day",
    f"{referrals['percentage_change']:+.2f}%",
    delta_color="inverse"
)

col3.metric(
    "Ward review waiting time",
    f"{ward_wait['to_be']:.2f} minutes",
    f"{ward_wait['percentage_change']:+.2f}%",
    delta_color="inverse"
)

col4.metric(
    "Reception waiting time",
    f"{reception_wait['to_be']:.2f} minutes",
    f"{reception_wait['percentage_change']:+.2f}%",
    delta_color="inverse"
)


# Waiting-time chart

st.divider()

st.subheader("Waiting Time: AS-IS vs TO-BE")

waiting_data = (
    kpi_data[kpi_data["category"] == "Waiting time"]
    [["metric", "as_is", "to_be"]]
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

waiting_chart = create_comparison_chart(
    data=waiting_data,
    label_column="Referral stage",
    value_column="Minutes",
    label_order=waiting_order,
    height=400
)

st.altair_chart(
    waiting_chart,
    width="stretch"
)

st.caption(
    "The TO-BE process reduces waiting time across "
    "all five referral stages."
)


# Patient-flow chart

st.divider()

st.subheader("Patient Flow: AS-IS vs TO-BE")

flow_data = (
    kpi_data[kpi_data["category"] == "Patient flow"]
    [["metric", "as_is", "to_be"]]
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

flow_chart = create_comparison_chart(
    data=flow_data,
    label_column="Measure",
    value_column="Average cases per day",
    label_order=flow_order,
    height=260
)

st.altair_chart(
    flow_chart,
    width="stretch"
)

st.caption(
    "The improved process treats more patients at Level 5 "
    "and sends fewer patients to Level 6."
)


# SQL pipeline table

st.divider()

with st.expander("View SQL pipeline output"):
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

st.divider()

st.subheader("Data Quality Checks")

total_rows = len(kpi_data)
missing_values = int(kpi_data.isna().sum().sum())
duplicate_rows = int(kpi_data.duplicated().sum())

quality1, quality2, quality3 = st.columns(3)

quality1.metric(
    "Rows loaded",
    total_rows
)

quality2.metric(
    "Missing values",
    missing_values
)

quality3.metric(
    "Duplicate rows",
    duplicate_rows
)

if missing_values == 0 and duplicate_rows == 0:
    st.success(
        "All checks passed. The data is complete "
        "and contains no duplicate rows."
    )
else:
    st.warning(
        "The data contains missing values or duplicate rows."
    )
