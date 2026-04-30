"""
algorithms.py
Disk Scheduling Algorithms Module
Contains: FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK
Each function returns: (seek_sequence, total_seek_time)
"""


def fcfs(requests: list[int], head: int, disk_size: int = 200) -> tuple[list[int], int]:
    """
    First Come First Served (FCFS)
    Services requests in the exact order they arrive.
    Simple but can result in high seek times.
    """
    seek_sequence = [head] + requests
    total_seek = sum(abs(seek_sequence[i] - seek_sequence[i - 1]) for i in range(1, len(seek_sequence)))
    return seek_sequence, total_seek


def sstf(requests: list[int], head: int, disk_size: int = 200) -> tuple[list[int], int]:
    """
    Shortest Seek Time First (SSTF)
    Always services the request closest to the current head position.
    Reduces average seek time but may cause starvation of far requests.
    """
    remaining = requests[:]
    seek_sequence = [head]
    current = head
    total_seek = 0

    while remaining:
        # Find nearest request to current head
        nearest = min(remaining, key=lambda x: abs(x - current))
        total_seek += abs(nearest - current)
        current = nearest
        seek_sequence.append(current)
        remaining.remove(nearest)

    return seek_sequence, total_seek


def scan(requests: list[int], head: int, disk_size: int = 200, direction: str = "right") -> tuple[list[int], int]:
    """
    SCAN (Elevator Algorithm)
    Head moves in one direction, services all requests in that direction,
    then reverses and services remaining requests.
    direction: 'right' (toward higher cylinders) or 'left'
    """
    seek_sequence = [head]
    total_seek = 0

    left = sorted([r for r in requests if r < head], reverse=True)
    right = sorted([r for r in requests if r >= head])

    if direction == "right":
        # Service right side first, then go to 0 end on reversal
        for track in right:
            seek_sequence.append(track)
        if left:
            # Reverse and go left
            for track in left:
                seek_sequence.append(track)
    else:
        # Service left side first
        for track in left:
            seek_sequence.append(track)
        if right:
            for track in right:
                seek_sequence.append(track)

    total_seek = sum(abs(seek_sequence[i] - seek_sequence[i - 1]) for i in range(1, len(seek_sequence)))
    return seek_sequence, total_seek


def cscan(requests: list[int], head: int, disk_size: int = 200, direction: str = "right") -> tuple[list[int], int]:
    """
    Circular SCAN (C-SCAN)
    Head moves in one direction, services requests, then jumps to the beginning
    without servicing on the return trip. Provides more uniform wait time.
    """
    seek_sequence = [head]
    total_seek = 0

    left = sorted([r for r in requests if r < head], reverse=True)
    right = sorted([r for r in requests if r >= head])

    if direction == "right":
        # Go right to end, jump to 0, continue right
        for track in right:
            seek_sequence.append(track)
        if left:
            # Jump: go to disk end then to 0 then service left (now going right from 0)
            seek_sequence.append(disk_size - 1)
            seek_sequence.append(0)
            for track in reversed(left):  # service them left-to-right
                seek_sequence.append(track)
    else:
        # Go left to 0, jump to end, continue left
        for track in left:
            seek_sequence.append(track)
        if right:
            seek_sequence.append(0)
            seek_sequence.append(disk_size - 1)
            for track in reversed(right):
                seek_sequence.append(track)

    total_seek = sum(abs(seek_sequence[i] - seek_sequence[i - 1]) for i in range(1, len(seek_sequence)))
    return seek_sequence, total_seek


def look(requests: list[int], head: int, disk_size: int = 200, direction: str = "right") -> tuple[list[int], int]:
    """
    LOOK Algorithm
    Like SCAN but the head only goes as far as the last request in each direction
    (doesn't travel all the way to the disk boundary).
    """
    seek_sequence = [head]

    left = sorted([r for r in requests if r < head], reverse=True)
    right = sorted([r for r in requests if r >= head])

    if direction == "right":
        for track in right:
            seek_sequence.append(track)
        for track in left:
            seek_sequence.append(track)
    else:
        for track in left:
            seek_sequence.append(track)
        for track in right:
            seek_sequence.append(track)

    total_seek = sum(abs(seek_sequence[i] - seek_sequence[i - 1]) for i in range(1, len(seek_sequence)))
    return seek_sequence, total_seek


def clook(requests: list[int], head: int, disk_size: int = 200, direction: str = "right") -> tuple[list[int], int]:
    """
    Circular LOOK (C-LOOK)
    Like C-SCAN but head only goes as far as the last request in each direction.
    Most efficient version of SCAN family.
    """
    seek_sequence = [head]

    left = sorted([r for r in requests if r < head], reverse=True)
    right = sorted([r for r in requests if r >= head])

    if direction == "right":
        for track in right:
            seek_sequence.append(track)
        if left:
            # Jump directly to the smallest left request (no disk boundary travel)
            for track in reversed(left):
                seek_sequence.append(track)
    else:
        for track in left:
            seek_sequence.append(track)
        if right:
            for track in reversed(right):
                seek_sequence.append(track)

    total_seek = sum(abs(seek_sequence[i] - seek_sequence[i - 1]) for i in range(1, len(seek_sequence)))
    return seek_sequence, total_seek


def run_all(requests: list[int], head: int, disk_size: int = 200, direction: str = "right") -> dict:
    """
    Run all six algorithms and return a dict of results.
    Returns: { algo_name: { 'sequence': [...], 'total': int, 'avg': float } }
    """
    algorithms = {
        "FCFS": fcfs,
        "SSTF": sstf,
        "SCAN": scan,
        "C-SCAN": cscan,
        "LOOK": look,
        "C-LOOK": clook,
    }
    results = {}
    for name, fn in algorithms.items():
        if name in ("FCFS", "SSTF"):
            seq, total = fn(requests, head, disk_size)
        else:
            seq, total = fn(requests, head, disk_size, direction)
        results[name] = {
            "sequence": seq,
            "total": total,
            "avg": round(total / len(requests), 2) if requests else 0,
        }
    return results
