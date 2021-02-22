import pytest
import sys

if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, patch
else:                         # pragma: no cover
    from mock import Mock, patch

from odin.adapters.metadata_writer import MetadataWriterAdapter


class MetadataWriterTestFixture(object):

    def __init__(self):
        self.adapter = MetadataWriterAdapter()
        self.path = ''
        self.put_path = ''
        self.request = Mock()
        self.request.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.request.body = '{"file": "testFile.h5"}'
        self.mutable_dict = {
            'extra': 'wibble',
            'bonus': 'win',
            'nest': {
                'double_nest': {
                    'nested_val': 125,
                    'dont_touch': "let me stay!"
                }
            }
        }

@pytest.fixture(scope="class")
def test_metadata_adapter():
    """Fixture used in the Medatadata Adapter test cases"""
    test_metadata_writer_adapter = MetadataWriterTestFixture()
    yield test_metadata_writer_adapter


class TestMetadataWriterAdapter():

    def test_adapter_get(self, test_metadata_adapter):
        """Test the GET call of the adapter"""

        response = test_metadata_adapter.adapter.get(
            test_metadata_adapter.path, test_metadata_adapter.request
        )

        assert type(response.data) == dict
        assert "file" in response.data
        assert response.status_code == 200

    def test_adapter_get_bad_path(self, test_metadata_adapter):
        
        bad_path = "/bad/path"
        expected_response = {'error': 'Invalid path: {}'.format(bad_path)}

        response = test_metadata_adapter.adapter.get(bad_path, test_metadata_adapter.request)

        assert response.data == expected_response
        assert response.status_code == 400

    def test_adapter_put(self, test_metadata_adapter):

        response = test_metadata_adapter.adapter.put(
            test_metadata_adapter.put_path, test_metadata_adapter.request
        )

        assert "file" in response.data
        assert response.data["file"] == "testFile.h5"
        assert response.status_code == 200

    def test_metadata_put(self, test_metadata_adapter):
        
        expected_response = {"metadata": {"test": "Test Metadata"}}

        test_metadata_adapter.request.body = expected_response['metadata']
        test_metadata_adapter.put_path = "metadata"
        response = test_metadata_adapter.adapter.put(
            test_metadata_adapter.put_path, test_metadata_adapter.request
        )

        assert response.data == expected_response
        assert response.status_code == 200

    def test_metadata_long_path_put(self, test_metadata_adapter):

        expected_response = {"deeper": {"nested_val": 125}}
        test_metadata_adapter.put_path = "metadata/goDeep/deeper"
        test_metadata_adapter.request.body = {'nested_val': 125}

        response = test_metadata_adapter.adapter.put(
            test_metadata_adapter.put_path, test_metadata_adapter.request
        )
        print(test_metadata_adapter.adapter.metadata_writer.get("metadata"))
        assert response.data == expected_response
        assert response.status_code == 200

    def test_metadata_write_metadata(self, test_metadata_adapter):
        # how we mocking out the file?
        with patch("odin.adapters.metadata_writer.h5py") as mock_h5py:

            test_metadata_adapter.put_path = "write"

            response = test_metadata_adapter.adapter.put(
                test_metadata_adapter.put_path, test_metadata_adapter.request
            )

            mock_h5py.File.assert_called_with(
                test_metadata_adapter.adapter.metadata_writer.file_name, 'r+'
            )

            # mock_h5py.File.create_group.assert_called_with('metadata')