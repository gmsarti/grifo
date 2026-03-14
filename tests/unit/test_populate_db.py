import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from scripts.populate_db import populate_from_directory

@patch("scripts.populate_db.VectorStoreManager")
def test_populate_from_directory(mock_manager_class, tmp_path):
    """Test the populate_from_directory function."""
    # Setup mock
    mock_manager = mock_manager_class.return_value
    
    # Create temp files
    d = tmp_path / "test_ingestion"
    d.mkdir()
    (d / "test1.pdf").write_text("content")
    (d / "test2.txt").write_text("content")
    (d / "invalid.exe").write_text("content")
    
    # Run
    populate_from_directory(str(d))
    
    # Verify manager was instantiated
    mock_manager_class.assert_called_once()
    
    # Verify ingest_file was called for valid files
    assert mock_manager.ingest_file.call_count == 2
    
    # Check calls
    calls = [str(d / "test1.pdf"), str(d / "test2.txt")]
    actual_calls = [call[0][0] for call in mock_manager.ingest_file.call_args_list]
    for expected in calls:
        assert expected in actual_calls

def test_populate_non_existent_directory():
    """Test with non-existent directory."""
    with patch("scripts.populate_db.logger") as mock_logger:
        populate_from_directory("/non/existent/path")
        mock_logger.error.assert_called_once()
