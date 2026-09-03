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

st.divider()

st.subheader("SQL Pipeline Output")

st.dataframe(
    kpi_data,
    hide_index=True,
    width="stretch"
)

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

waiting_data["Referral stage"] = waiting_data["Referral stage"].replace({
    "Ward review queue": "Ward review",
    "Speciality availability queue": "Speciality check",
    "External transport request queue": "Transport request",
    "Transport coordination queue": "Transport coordination",
    "Reception queue": "Reception"
})

st.bar_chart(
    waiting_data,
    x="Referral stage",
    y=["AS-IS", "TO-BE"],
    x_label="Referral stage",
    y_label="Minutes",
    color=["#EF4444", "#10B981"],
    horizontal=True,
    stack=False,
    height=450
)

st.caption(
    "Red shows the current AS-IS process. "
    "Green shows the improved TO-BE process."
)
