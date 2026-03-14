import os
import sys
import argparse
from pathlib import Path

# Add project root to path to allow imports from app
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

from app.data_source.vector_store import VectorStoreManager
from app.core.logging import get_logger

logger = get_logger(__name__)

def populate_from_directory(directory_path: str):
    """
    Reads all supported files from the directory and ingests them into the vector store.
    """
    path = Path(directory_path)
    if not path.exists() or not path.is_dir():
        logger.error(f"Directory not found: {directory_path}")
        return

    manager = VectorStoreManager()
    
    # Supported extensions based on loaders.py
    extensions = {'.pdf', '.docx', '.csv', '.txt', '.md'}
    
    files_to_process = [f for f in path.iterdir() if f.suffix.lower() in extensions]
    
    if not files_to_process:
        logger.warning(f"No valid files found in {directory_path}")
        return

    logger.info(f"Starting ingestion of {len(files_to_process)} files from {directory_path}...")
    
    for file_path in files_to_process:
        try:
            logger.info(f"Processing: {file_path.name}")
            manager.ingest_file(str(file_path))
            logger.info(f"Successfully ingested: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to ingest {file_path.name}: {str(e)}")

    logger.info("Population process completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate vector store from a directory of files.")
    parser.add_argument(
        "--dir", 
        type=str, 
        default="pdfs_to_test_ingestion",
        help="Directory containing files to ingest (default: pdfs_to_test_ingestion)"
    )
    
    args = parser.parse_args()
    
    # Run the population
    populate_from_directory(args.dir)
