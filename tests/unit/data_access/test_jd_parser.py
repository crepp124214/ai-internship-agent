import pytest
import pandas as pd
from io import BytesIO
from src.data_access.parsers.jd_parser import JDParser, JDParseResult


class TestJDParser:
    def test_parse_result(self):
        result = JDParseResult(
            title="Python Developer",
            company="TechCorp",
            description="We need a Python developer",
        )

        assert result.title == "Python Developer"
        assert result.company == "TechCorp"

    def test_parse_csv_basic(self):
        csv_content = b"title,company,description\nPython Developer,TechCorp,We need Python"
        parser = JDParser()
        results = parser._parse_csv(csv_content)

        assert len(results) == 1
        assert results[0].title == "Python Developer"
        assert results[0].company == "TechCorp"

    def test_find_column(self):
        parser = JDParser()
        columns = ['job_title', 'company_name', 'description']

        assert parser._find_column('title', columns) == 'job_title'
        assert parser._find_column('company', columns) == 'company_name'

    def test_parse_excel_basic(self):
        import pandas as pd
        df = pd.DataFrame({
            'title': ['Python Developer'],
            'company': ['TechCorp'],
            'description': ['We need Python'],
        })
        parser = JDParser()
        results = parser._parse_dataframe(df)

        assert len(results) == 1
        assert results[0].title == "Python Developer"

    def test_unsupported_format(self):
        parser = JDParser()
        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse_file(b"content", "jobs.txt")