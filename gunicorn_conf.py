import multiprocessing

workers = int(multiprocessing.cpu_count() * 2) + 1
threads = 4
timeout = 120
bind = "0.0.0.0:8000"