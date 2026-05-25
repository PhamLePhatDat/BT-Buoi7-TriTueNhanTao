from builtins import range, set, sum
import heapq
import re
import random
from collections import deque

actions   = ["U", "D", "L", "R"]
goal      = [[1, 2, 3], [4, 0, 5], [6, 7, 8]]

DFS_MAX_DEPTH = 1000


def find_zero(state):
    for i in range(3):
        for j in range(3):
            if state[i][j] == 0:
                return i, j


def to_tuple(state):
    return tuple(tuple(row) for row in state)


def move(state, action):
    r, c = find_zero(state)
    ns = [row[:] for row in state]
    if   action == "U" and r > 0: ns[r][c], ns[r-1][c] = ns[r-1][c], ns[r][c]
    elif action == "D" and r < 2: ns[r][c], ns[r+1][c] = ns[r+1][c], ns[r][c]
    elif action == "L" and c > 0: ns[r][c], ns[r][c-1] = ns[r][c-1], ns[r][c]
    elif action == "R" and c < 2: ns[r][c], ns[r][c+1] = ns[r][c+1], ns[r][c]
    return ns


def _count_inversions(state):
    flat = [x for row in state for x in row if x != 0]
    return sum(flat[i] > flat[j]
               for i in range(len(flat))
               for j in range(i + 1, len(flat)))


def is_solvable(initial_state, goal_state=None):
    if goal_state is None:
        goal_state = goal
    return _count_inversions(initial_state) % 2 == _count_inversions(goal_state) % 2


def parse_state(text):
    nums = list(map(int, re.findall(r'\d+', text)))
    if len(nums) != 9:
        raise ValueError(f"Cần đúng 9 số, nhận được {len(nums)}")
    if sorted(nums) != list(range(9)):
        raise ValueError("Cần đủ các số từ 0 đến 8, không trùng lặp")
    return [nums[i*3:(i+1)*3] for i in range(3)]


def random_state(goal_state=None):
    if goal_state is None:
        goal_state = goal
    nums = list(range(9))
    while True:
        random.shuffle(nums)
        state = [nums[i*3:(i+1)*3] for i in range(3)]
        if is_solvable(state, goal_state) and state != goal_state:
            return state

class Node:
    def __init__(self, state, parent=None, cost=0, action="" ,step = 0):
        self.state  = state
        self.parent = parent
        self.cost   = cost
        self.action = action
        self.step = step

    def __lt__(self, other):
        return self.cost < other.cost


def bfs(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal

    root = Node(initial_state)
    if root.state == goal_state:
        return root

    frontier        = deque([root])
    explored        = set()
    frontier_states = {to_tuple(initial_state)}

    while frontier:
        if stop_flag and stop_flag():
            return None

        node       = frontier.popleft()
        node_tuple = to_tuple(node.state)
        frontier_states.discard(node_tuple)
        explored.add(node_tuple)

        for action in actions:
            child_state = move(node.state, action)
            child_tuple = to_tuple(child_state)
            if child_tuple not in explored and child_tuple not in frontier_states:
                child = Node(child_state, node, node.cost + 1, action)
                if child_state == goal_state:
                    return child
                frontier.append(child)
                frontier_states.add(child_tuple)

    return None

def dfs(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal

    root = Node(initial_state)

    if root.state == goal_state:
        return root

    frontier = [root]
    frontier_states = {to_tuple(initial_state)}
    explored = set()

    while frontier:
        if stop_flag and stop_flag():          #Huỷ khi UI yêu cầu
            return None

        node = frontier.pop()
        node_tuple = to_tuple(node.state)
        frontier_states.discard(node_tuple)
        explored.add(node_tuple)

        if node.cost >= DFS_MAX_DEPTH:
            continue

        for action in actions:
            child_state = move(node.state, action)

            if child_state == node.state:
                continue

            child = to_tuple(child_state)
            if child not in explored and child not in frontier_states:
                child_node = Node(child_state, node, node.cost + 1, action)
                if child_state == goal_state:
                    return child_node
                frontier.append(child_node)
                frontier_states.add(child)
    return None

def ids(initial_state, goal_state=None, stop_flag=None):
    if goal_state is None:
        goal_state = goal

    t = 0
    while True:
        if stop_flag and stop_flag():
            return None
        result = _depth_limited_search(initial_state, goal_state, limit=t,
                                       stop_flag=stop_flag)
        if result != "cutoff":
            return result
        t += 1


def _depth_limited_search(initial_state, goal_state, limit, stop_flag=None):
    found_cutoff = False
    root = Node(initial_state)

    if root.state == goal_state:
        return root

    initial_tuple = to_tuple(initial_state)
    stack = [(root, {initial_tuple})]

    while stack:
        if stop_flag and stop_flag():
            return None

        node, path_set = stack.pop()

        if node.state == goal_state:
            return node

        if node.cost >= limit:
            found_cutoff = True
            continue

        for action in actions:
            child_state = move(node.state, action)
            child_tuple = to_tuple(child_state)

            if child_tuple in path_set:
                continue

            child_node = Node(child_state, node, node.cost + 1, action)

            if child_state == goal_state:
                return child_node

            child_path_set = path_set | {child_tuple}
            stack.append((child_node, child_path_set))

    return "cutoff" if found_cutoff else None

def ucs_cost(state, goal_state, step=0):
    if goal_state is None:
        goal_state = goal
    if state == goal_state:
        return step
    
    cost = 0
    for i in range(3):
        for j in range(3):
            if state[i][j] == goal_state[i][j]:
                continue
            cost += 1
    return cost + step

def ucs(initial_state, goal_state=None, stop_flag=None):

    if goal_state is None:
        goal_state = goal

    if initial_state == goal_state:
        return Node(initial_state)

    root = Node(
        initial_state,
        cost=ucs_cost(initial_state, goal_state, step=0),
        step=0,
    )

    frontier = []
    heapq.heappush(frontier, (root.cost, root))

    explored = set()
    frontier_states = {to_tuple(initial_state)}

    while frontier:
        if stop_flag and stop_flag():
            return None

        _, node = heapq.heappop(frontier)
        node_tuple = to_tuple(node.state)
        frontier_states.discard(node_tuple)

        if node_tuple in explored:
            continue
        explored.add(node_tuple)

        if node.state == goal_state:
            return node

        for action in actions:
            child_state = move(node.state, action)
            if child_state == node.state:
                continue
            child_tuple = to_tuple(child_state)
            if child_tuple not in explored:
                child_step = node.step + 1
                child_cost = ucs_cost(child_state, goal_state, step=child_step)
                child_node = Node(child_state, node, child_cost, action, child_step)
                if child_state == goal_state:
                    return child_node
                heapq.heappush(frontier, (child_node.cost, child_node))
                frontier_states.add(child_tuple)
    return None

def get_path(node):
    path = []
    while node.parent is not None:
        path.append((node.action, node.state))
        node = node.parent
    path.append(("Start", node.state))
    path.reverse()
    return path