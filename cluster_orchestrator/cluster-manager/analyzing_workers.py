from datetime import datetime

from mongodb_client import find_all_nodes


def looking_for_dead_workers(interval):
    nodes = find_all_nodes()


