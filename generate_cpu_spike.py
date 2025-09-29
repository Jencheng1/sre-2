#!/usr/bin/env python3
"""
Generate CPU spike for SRE demo
Creates realistic CPU usage patterns to trigger alerts
"""
import multiprocessing
import time
import math
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def cpu_intensive_task(duration=30):
    """Run CPU intensive calculations"""
    start_time = time.time()
    while (time.time() - start_time) < duration:
        # Perform intensive calculations
        for i in range(1000):
            math.sqrt(random.randint(1, 1000000))
            math.factorial(random.randint(10, 20))
            [j**2 for j in range(100)]

def generate_cpu_spike(cores=None, duration=60, intensity=0.8):
    """
    Generate CPU spike across multiple cores
    
    Args:
        cores: Number of cores to use (None = all available)
        duration: How long to run the spike (seconds)
        intensity: CPU usage intensity (0.0 to 1.0)
    """
    if cores is None:
        cores = multiprocessing.cpu_count()
    
    # Adjust cores based on intensity
    active_cores = max(1, int(cores * intensity))
    
    logger.info(f"Starting CPU spike demo...")
    logger.info(f"- Using {active_cores} out of {cores} available cores")
    logger.info(f"- Duration: {duration} seconds")
    logger.info(f"- Target intensity: {intensity * 100}%")
    
    # Create processes
    processes = []
    for i in range(active_cores):
        p = multiprocessing.Process(target=cpu_intensive_task, args=(duration,))
        p.start()
        processes.append(p)
        logger.info(f"Started CPU load process {i+1}/{active_cores}")
    
    # Monitor and wait
    logger.info("CPU spike in progress...")
    time.sleep(duration)
    
    # Ensure all processes complete
    for p in processes:
        p.join()
    
    logger.info("CPU spike completed!")

if __name__ == "__main__":
    # Generate a 90-second CPU spike at 80% intensity
    generate_cpu_spike(duration=90, intensity=0.8)