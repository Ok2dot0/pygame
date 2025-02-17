import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
import pandas as pd

class LogAnalyzer:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.log_sets = self.get_log_sets()

    def get_log_sets(self):
        """Get all sets of log files grouped by timestamp"""
        log_sets = {}
        for file in os.listdir(self.log_dir):
            if file.startswith("log_"):
                timestamp = file.split("_")[1]
                if timestamp not in log_sets:
                    log_sets[timestamp] = []
                log_sets[timestamp].append(os.path.join(self.log_dir, file))
        return log_sets

    def load_log_data(self, timestamp):
        """Load all log data for a specific timestamp"""
        data = {
            'general': [],
            'performance': {},
            'entities': {},
            'events': {}
        }
        
        for file in self.log_sets[timestamp]:
            if file.endswith("general.log"):
                with open(file, 'r') as f:
                    data['general'] = f.readlines()
            elif file.endswith("performance.json"):
                with open(file, 'r') as f:
                    data['performance'] = json.load(f)
            elif file.endswith("entities.json"):
                with open(file, 'r') as f:
                    data['entities'] = json.load(f)
            elif file.endswith("events.json"):
                with open(file, 'r') as f:
                    data['events'] = json.load(f)
        return data

    def plot_performance(self, data):
        """Plot performance metrics"""
        plt.figure(figsize=(12, 6))
        for operation, measurements in data['performance'].items():
            times = [datetime.strptime(m['timestamp'], '%H:%M:%S.%f') for m in measurements]
            durations = [m['duration'] for m in measurements]
            plt.plot(times, durations, label=operation, marker='o')
        
        plt.title("Performance Metrics Over Time")
        plt.xlabel("Time")
        plt.ylabel("Duration (ms)")
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def plot_entity_counts(self, data):
        """Plot entity counts over time"""
        plt.figure(figsize=(12, 6))
        for entity_type, counts in data['entities'].items():
            times = [datetime.strptime(c['timestamp'], '%H:%M:%S.%f') for c in counts]
            values = [c['count'] for c in counts]
            plt.plot(times, values, label=entity_type, marker='o')
        
        plt.title("Entity Counts Over Time")
        plt.xlabel("Time")
        plt.ylabel("Count")
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

class LogViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Game Log Analyzer")
        self.geometry("1200x800")
        
        self.analyzer = LogAnalyzer()
        
        self.create_widgets()

    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create session selector
        ttk.Label(main_frame, text="Select Session:").pack()
        self.session_var = tk.StringVar()
        session_select = ttk.Combobox(main_frame, textvariable=self.session_var)
        session_select['values'] = list(self.analyzer.log_sets.keys())
        session_select.pack()
        session_select.bind('<<ComboboxSelected>>', self.load_session)

        # Create notebook for different views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create tabs
        self.general_tab = ttk.Frame(self.notebook)
        self.performance_tab = ttk.Frame(self.notebook)
        self.entities_tab = ttk.Frame(self.notebook)
        self.events_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.general_tab, text='General Log')
        self.notebook.add(self.performance_tab, text='Performance')
        self.notebook.add(self.entities_tab, text='Entities')
        self.notebook.add(self.events_tab, text='Events')

        # Add text widgets
        self.general_text = tk.Text(self.general_tab)
        self.general_text.pack(fill=tk.BOTH, expand=True)

        # Add buttons for plots
        ttk.Button(self.performance_tab, text="Show Performance Plot", 
                  command=self.show_performance_plot).pack()
        ttk.Button(self.entities_tab, text="Show Entity Counts Plot", 
                  command=self.show_entity_plot).pack()

    def load_session(self, event=None):
        timestamp = self.session_var.get()
        self.current_data = self.analyzer.load_log_data(timestamp)
        
        # Update general log text
        self.general_text.delete(1.0, tk.END)
        for line in self.current_data['general']:
            self.general_text.insert(tk.END, line)

    def show_performance_plot(self):
        if hasattr(self, 'current_data'):
            self.analyzer.plot_performance(self.current_data)

    def show_entity_plot(self):
        if hasattr(self, 'current_data'):
            self.analyzer.plot_entity_counts(self.current_data)

if __name__ == "__main__":
    app = LogViewer()
    app.mainloop()
