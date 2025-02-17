import time
import traceback
from typing import Dict, Any
from datetime import datetime
import cProfile
import io
import pstats
import os
import json
import matplotlib.pyplot as plt

class DebugLogger:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    
    def __init__(self):
        # Create logs directory if it doesn't exist
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create log files with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_base = f"{self.log_dir}/log_{timestamp}"
        self.general_log = f"{self.log_base}_general.log"
        self.performance_log = f"{self.log_base}_performance.json"
        self.entity_log = f"{self.log_base}_entities.json"
        self.event_log_file = f"{self.log_base}_events.json"
        
        # Initialize other attributes
        self.start_time = time.time()
        self.performance_metrics = {}
        self.event_log = {}
        self.profiler = cProfile.Profile()
        self.entity_counts = {}
        self.debug_sections = set()
        
    def start_profiling(self):
        self.profiler.enable()
        
    def stop_profiling(self):
        self.profiler.disable()
        s = io.StringIO()
        stats = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
        stats.print_stats()
        print(s.getvalue())

    def _write_to_log(self, message: str):
        """Write a message to the general log file"""
        with open(self.general_log, 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")

    def trace(self, message: str) -> None:
        """
        Print a detailed trace message with timestamp and call location.
        
        :param message: The message to log
        :return: None
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        stack = traceback.extract_stack()
        caller = stack[-2]  # Get the caller's frame
        location = f"{caller.filename}:{caller.lineno}"
        log_msg = f"[TRACE][{timestamp}][{location}] {message}"
        print(f"{self.HEADER}{log_msg}{self.ENDC}")
        self._write_to_log(log_msg)

    def info(self, message: str, section: str = None) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if section:
            self.debug_sections.add(section)
            log_msg = f"[INFO][{timestamp}][{section}] {message}"
            print(f"{self.BLUE}{log_msg}{self.ENDC}")
        else:
            log_msg = f"[INFO][{timestamp}] {message}"
            print(f"{self.BLUE}{log_msg}{self.ENDC}")
        self._write_to_log(log_msg)
    
    def success(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_msg = f"[SUCCESS][{timestamp}] {message}"
        print(f"{self.GREEN}{log_msg}{self.ENDC}")
        self._write_to_log(log_msg)
    
    def warning(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_msg = f"[WARNING][{timestamp}] {message}"
        print(f"{self.WARNING}{log_msg}{self.ENDC}")
        self._write_to_log(log_msg)
    
    def error(self, message: str, exc_info=None) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        error_msg = f"{self.FAIL}[ERROR][{timestamp}] {message}{self.ENDC}"
        if exc_info:
            error_msg += f"\n{self.FAIL}{traceback.format_exc()}{self.ENDC}"
        print(error_msg)
        self._write_to_log(error_msg)

    def log_event(self, category: str, event: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if category not in self.event_log:
            self.event_log[category] = []
        self.event_log[category].append((timestamp, event))
        self.info(f"{category}: {event}", "Events")
        
        # Write event data to JSON
        with open(self.event_log_file, 'w') as f:
            json.dump(self.event_log, f, indent=2)

    def log_performance(self, operation: str, start_time: float) -> None:
        duration = (time.time() - start_time) * 1000
        self.performance_metrics[operation] = self.performance_metrics.get(operation, [])
        self.performance_metrics[operation].append({
            'timestamp': datetime.now().strftime('%H:%M:%S.%f'),
            'duration': duration
        })
        self.info(f"Performance - {operation}: {duration:.2f}ms", "Performance")
        
        # Write performance data to JSON
        with open(self.performance_log, 'w') as f:
            json.dump(self.performance_metrics, f, indent=2)

    def track_entity(self, entity_type: str, count: int) -> None:
        timestamp = datetime.now().strftime('%H:%M:%S.%f')
        if entity_type not in self.entity_counts:
            self.entity_counts[entity_type] = []
        self.entity_counts[entity_type].append({
            'timestamp': timestamp,
            'count': count
        })
        self.info(f"Entity count - {entity_type}: {count}", "Entities")
        
        # Write entity data to JSON
        with open(self.entity_log, 'w') as f:
            json.dump(self.entity_counts, f, indent=2)

    def dump_debug_info(self) -> None:
        print("\n=== Debug Information Dump ===")
        print("\nPerformance Metrics:")
        for op, duration in self.performance_metrics.items():
            print(f"{op}: {duration:.2f}ms")
        
        print("\nEntity Counts:")
        for entity_type, count in self.entity_counts.items():
            print(f"{entity_type}: {count}")
        
        print("\nEvent Log:")
        for category, events in self.event_log.items():
            print(f"\n{category}:")
            for timestamp, event in events:
                print(f"  [{timestamp}] {event}")

logger = DebugLogger()
