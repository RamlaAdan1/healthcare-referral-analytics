import unittest

import duckdb

from data_pipeline import DATABASE_FILE, build_data_pipeline


class TestDataPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        build_data_pipeline()

        with duckdb.connect(
            str(DATABASE_FILE),
            read_only=True
        ) as connection:

            cls.kpi_data = connection.execute("""
                SELECT *
                FROM referral_kpis
            """).df()

    def test_seven_kpis_are_created(self):
        self.assertEqual(
            len(self.kpi_data),
            7
        )

    def test_required_columns_exist(self):
        required_columns = {
            "metric",
            "category",
            "as_is",
            "to_be",
            "unit",
            "percentage_change"
        }

        self.assertTrue(
            required_columns.issubset(
                self.kpi_data.columns
            )
        )

    def test_no_missing_values(self):
        missing_values = int(
            self.kpi_data.isna().sum().sum()
        )

        self.assertEqual(
            missing_values,
            0
        )

    def test_metric_names_are_unique(self):
        duplicate_metrics = int(
            self.kpi_data.duplicated(
                subset=["metric"]
            ).sum()
        )

        self.assertEqual(
            duplicate_metrics,
            0
        )


if __name__ == "__main__":
    unittest.main()
