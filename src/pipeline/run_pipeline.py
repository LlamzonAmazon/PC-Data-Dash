"""
Uses the Orchestrator class to run the entire data pipeline.

Fetch -> Clean -> Process -> Upload
"""

from src.pipeline.orchestrator import Orchestrator

def main():
    orchestrator = Orchestrator()
    processed_data = orchestrator.run()
    
    return processed_data

if __name__ == "__main__":
    main()
