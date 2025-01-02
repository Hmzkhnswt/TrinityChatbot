import subprocess
import sys
import os
from TrinityBot.utils.logging import logger
from dotenv import load_dotenv

load_dotenv()

def run_stage(stage_script: str):
    """
    Executes a pipeline stage script and ensures errors are properly logged and raised.

    Args:
        stage_script (str): The path to the stage script.
    """
    try:
        result = subprocess.run(
            [sys.executable, stage_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print(f"Error running {stage_script}:\n{result.stderr}")
            raise RuntimeError(f"{stage_script} failed with return code {result.returncode}")
        else:
            print(f"{stage_script} completed successfully.\nOutput:\n{result.stdout}")
    except Exception as e:
        print(f"An error occurred while running {stage_script}: {str(e)}")
        raise

def main():
    """
    Main function to orchestrate the pipeline execution.
    """
    print("<<<< Started Pipeline Execution ... >>>>")
    logger.info("<<<< Started Pipeline Execution ... >>>>")

    stage_scripts = [
        "src/TrinityBot/pipeline/stage01_DataScraping.py",
        "src/TrinityBot/pipeline/stage02_QdrantDumping.py"
    ]

    for script in stage_scripts:
        if not os.path.exists(script):
            print(f"Error: Script {script} not found.")
            sys.exit(1)
        run_stage(script)

    print("<<<< Started Pipeline Execution ... >>>>")
    logger.info("<<<< Pipeline Completed ... >>>>")

if __name__ == "__main__":
    main()
