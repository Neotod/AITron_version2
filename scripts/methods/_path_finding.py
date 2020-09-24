from ks.models import ECell, EDirection
from time import perf_counter

def get_costs(self, start_pos, dest_pos, ignore_cost):
    start_y, end_y = min(start_pos[0], dest_pos[0])-6, max(start_pos[0], dest_pos[0])+6
    start_x, end_x = min(start_pos[1], dest_pos[1])-6, max(start_pos[1], dest_pos[1])+6

    start_y = 1 if start_y < 1 else start_y
    end_y = len(self.board)-2 if end_y > len(self.board)-2 else end_y

    start_x = 1 if start_x < 1 else start_x
    end_x = len(self.board[0])-2 if end_x > len(self.board[0])-2 else end_x

    costs = {}
    for i in range(start_y, end_y+1):
        for j in range(start_x, end_x+1):
            if self.board[i][j] != ECell.AreaWall:
                for wall_type in list(self.walls.keys())[:-2]:
                    positions = self.walls[wall_type]
                    position = (i, j)
                    if position in positions:
                        costs[(i, j)] = self.get_wall_weight(position)
            else:
                if self.agent_state == 'suicide':
                    costs[(i, j)] = 0


        for wall_pos in costs:
            y, x = wall_pos[0], wall_pos[1]

            if self.agent_name == 'Blue':
                m_wall = ECell.BlueWall
                o_wall = ECell.YellowWall
            elif self.agent_name == 'Yellow':
                m_wall = ECell.YellowWall
                o_wall = ECell.BlueWall

            wall_cost = costs[wall_pos]

            if ignore_cost == False:
                if self.agent.wall_breaker_cooldown != 0:
                    if self.board[y][x] == o_wall or self.board[y][x] == m_wall:
                        wall_cost += (wall_cost * 40/100)
                        costs[wall_pos] = int(wall_cost)
                
                if self.agent_state == 'normal':
                    if self.board[y][x] == ECell.Empty:
                        wall_cost -= (wall_cost * 20/100)
                        costs[wall_pos] = int(wall_cost)

                if self.board[y][x] == m_wall:
                    wall_cost += (wall_cost * 60/100)
                    costs[wall_pos] = int(wall_cost)

                if wall_cost < 0:
                    print(f'there is a negative cost here: {wall_pos} | {wall_cost}')

    return costs

def get_heuristics(self, start_pos, dest_pos):
    start_y, end_y = min(start_pos[0], dest_pos[0])-6, max(start_pos[0], dest_pos[0])+6
    start_x, end_x = min(start_pos[1], dest_pos[1])-6, max(start_pos[1], dest_pos[1])+6

    start_y = 1 if start_y < 1 else start_y
    end_y = len(self.board)-2 if end_y > len(self.board)-2 else end_y

    start_x = 1 if start_x < 1 else start_x
    end_x = len(self.board[0])-2 if end_x > len(self.board[0])-2 else end_x

    heuristics = {}
    for i in range(start_y, end_y+1):
        for j in range(start_x, end_x+1):
            if self.board[i][j] != ECell.AreaWall:
                distance = abs(i - dest_pos[0]) + abs(j - dest_pos[1])
                heuristics[(i, j)] = distance*10

            else:
                if self.agent_state == 'suicide':
                    heuristics[(i, j)] = 0

    return heuristics

def find_best_route(self, start_pos, dest_pos, ignore_cost=False):
    start_y, end_y = min(start_pos[0], dest_pos[0])-6, max(start_pos[0], dest_pos[0])+6
    start_x, end_x = min(start_pos[1], dest_pos[1])-6, max(start_pos[1], dest_pos[1])+6

    start_y = 1 if start_y < 1 else start_y
    end_y = len(self.board)-2 if end_y > len(self.board)-2 else end_y
    
    start_x = 1 if start_x < 1 else start_x
    end_x = len(self.board[0])-2 if end_x > len(self.board[0])-2 else end_x

    
    heuristics = self.get_heuristics(start_pos, dest_pos)
    costs = self.get_costs(start_pos, dest_pos, ignore_cost)

    i, j = start_pos[0], start_pos[1]
    
    open_vertices = {(i, j): [0, []]}
    visited_vertices = {}
    
    cost_so_far = 0
    while True:
        next_node, min_f = (0, 0), 10000000000000
        for node, value in open_vertices.items():
            f = value[0]
            if f < min_f:
                next_node = node
                min_f = f
            elif f == min_f:
                node_h = heuristics[node]
                min_node_h = heuristics[next_node]
                if node_h < min_node_h:
                    next_node = node
                    min_f = f
        
        current_node = next_node
        try:
            came_from = open_vertices[current_node][1]
        except Exception as e:
            print(f'start {start_pos}, end: {dest_pos}')
            print(f'open vertices: {open_vertices}')
            print('Exception occured in  FIND_BEST_ROUTE')

                
        cost_so_far = 0
        for node in came_from:
            cost_so_far += costs[node]

        open_vertices.pop(current_node)

        i, j = current_node[0], current_node[1]
        neighbors = {}
        y_steps = [0, -1, 1, 0]
        x_steps = [1, 0, 0, -1]
        for l in range(4):
            ii = i + y_steps[l]
            jj = j + x_steps[l]
            
            if ii < start_y or ii > end_y or jj < start_x or jj > end_x:
                continue
            if self.board[ii][jj] == ECell.AreaWall and self.agent_state != 'suicide' and (ii, jj) != self.target_pos:
                continue
            if (ii, jj) == self.agent_prev_pos:
                continue

            opponent_pos = (self.opponent.position.y, self.opponent.position.x)
            if self.agent_state != 'brutal' and (ii, jj) == opponent_pos:
                continue

            node = (ii, jj)
            g = costs[node] + cost_so_far
            f = heuristics[node] + g
            
            neighbor_came_from = came_from.copy()
            neighbor_came_from.append(current_node)
            neighbors[node] = [f, neighbor_came_from]


        next_neighbors = []
        for node, value in neighbors.items():
            f = value[0]
            if node == dest_pos:
                path = came_from
                path.append(current_node)
                path.append(node)

                return path

            if node in list(open_vertices.keys()):
                visited_f = open_vertices[node][0]
                if f > visited_f:
                    continue
                elif f < visited_f:
                    node_value = open_vertices[node].copy()
                    del open_vertices[node]
                    open_vertices[node] = node_value

            elif node in list(visited_vertices.keys()):
                visited_f = visited_vertices[node][0]
                if f > visited_f:
                    continue
            else:
                open_vertices[node] = neighbors[node].copy()

        g = cost_so_far + costs[current_node]
        f = heuristics[current_node] + g
        visited_vertices[current_node] = [f, came_from]

def find_attack_routes(self, start_pos):
    range_y = [start_pos[0]-6, start_pos[0]+6]
    if range_y[0] < 1:
        range_y[0] = 1
    elif range_y[1] > len(self.board)-2:
        range_y[1] = len(self.board)-2
    y_range = range(range_y[0], range_y[1]+1)

    range_x = [start_pos[1]-6, start_pos[1]+6]
    if range_x[0] < 1:
        range_x[0] = 1
    elif range_x[1] > len(self.board[0])-2:
        range_x[1] = len(self.board[0])-2
    x_range = range(range_x[0], range_x[1]+1)
    
    if self.agent_name == 'Blue':
        my_wall = ECell.BlueWall
        opponent_wall = ECell.YellowWall
    elif self.agent_name == 'Yellow':
        my_wall = ECell.YellowWall
        opponent_wall = ECell.BlueWall

    wall_breaker_rem_time = self.agent.wall_breaker_rem_time
    if self.agent.wall_breaker_cooldown == 0:
        wall_breaker_rem_time = 6

    routes = {(start_pos, ): ['open', 1]}
    while True:
        for route in routes.copy():
            route_state = routes[route][0]

            if route_state != 'closed':
                last_pos = route[len(route)-1]

                y_steps = (0, 1, -1, 0)
                x_steps = (1, 0, 0, -1)
                for i in range(4):
                    y = last_pos[0] + y_steps[i]
                    x = last_pos[1] + x_steps[i]
                    
                    if self.board[y][x] == ECell.AreaWall:
                        continue
                    if y not in y_range or x not in x_range:
                        continue
                    if (y, x) in route:
                        continue

                    if self.board[y][x] == opponent_wall:
                        if len(route) <= wall_breaker_rem_time - 1:
                            new_route = list(route) + [(y, x)]
                            routes[tuple(new_route)] = [route_state, len(new_route)]
                    
                    elif self.board[y][x] == ECell.Empty:
                        if 3 <= len(route) and len(route) <= wall_breaker_rem_time:
                            new_route = list(route) + [(y, x)]
                            route_opp_walls = routes[route][1]
                            routes[tuple(new_route)] = ['closed', route_opp_walls]

                del routes[route]

        opened_routes = 0
        for route in routes:
            route_state = routes[route][0]
            
            if route_state == 'open':
                opened_routes += 1

        if opened_routes == 0:
            break
    
    routes = {route: ['open', 1, routes[route][1]] for route in routes}
    while True:
        for route in routes.copy():
            route_state = routes[route][0]
            opponent_walls = routes[route][2]

            if route_state != 'closed':
                last_pos = route[len(route)-1]

                y_steps = [0, 1, -1, 0]
                x_steps = [1, 0, 0, -1]
                empty_walls = []
                for i in range(4):
                    y = last_pos[0] + y_steps[i]
                    x = last_pos[1] + x_steps[i]
                    
                    if self.board[y][x] == ECell.AreaWall:
                        continue
                    if (y, x) in route:
                        continue
                    if (y, x) == self.agent_pos:
                        continue
                    if self.board[y][x] == ECell.Empty:
                        empty_walls.append((y, x))

                if len(empty_walls) != 0:
                    for empty_wall in empty_walls:
                        route_copy = list(route)
                        new_route = route_copy + [empty_wall]

                        route_empty_walls = routes[route][1] + 1
                        route_opp_walls = routes[route][2]
                        wanted_empty_walls = 12 - route_opp_walls - (6 - wall_breaker_rem_time)
                        if route_empty_walls == wanted_empty_walls:
                            routes[tuple(new_route)] = ['closed', wanted_empty_walls, route_opp_walls]
                        else:
                            routes[tuple(new_route)] = ['open', route_empty_walls, route_opp_walls]

                del routes[route]

        opened_routes = 0
        for route in routes:
            route_state = routes[route][0]
            
            if route_state == 'open':
                opened_routes += 1
        if opened_routes == 0:
            break

    closed_routes = {}
    for route in routes:
        opponent_walls = routes[route][2]
        closed_routes[route] = opponent_walls

    return closed_routes

def choose_best_attack_route(self, routes):
    if self.agent_name == 'Blue':
        my_wall = ECell.BlueWall
        opponent_wall = ECell.YellowWall
    elif self.agent_name == 'Yellow':
        my_wall = ECell.YellowWall
        opponent_wall = ECell.BlueWall

    wall_breaker_rem_time = self.agent.wall_breaker_rem_time
    if self.agent.wall_breaker_cooldown == 0:
        wall_breaker_rem_time = 6

    acceptable_routes = {route: routes[route] for route in routes if routes[route] <= wall_breaker_rem_time}
    routes = acceptable_routes
    if len(acceptable_routes) == 0:
        return None

    routes_opp_walls = [routes[route] for route in routes]
    max_opp_walls = max(routes_opp_walls)

    max_opp_walls_routes = [route for route in routes if routes[route] == max_opp_walls]
    routes = max_opp_walls_routes

    route_weights = {}
    walls_neighbors_weight = {}
    for route in routes:
        route_part_2 = route[max_opp_walls:]

        weight_sum = 0
        for wall_pos in route_part_2:
            if wall_pos in walls_neighbors_weight:
                wall_weight = walls_neighbors_weight[wall_pos]
            else:
                wall_weight = self.get_wall_neighbors_weight(wall_pos)
                walls_neighbors_weight[wall_pos] = wall_weight

            weight_sum += wall_weight

        change_percentage = ((10 // weight_sum)/100)

        last_pos = route[-1]

        range_y = [last_pos[0]-2, last_pos[0]+2]
        if range_y[0] < 1:
            range_y[0] = 1
        elif range_y[1] > len(self.board)-2:
            range_y[1] = len(self.board)-2
        y_range = range(range_y[0], range_y[1]+1)

        range_x = [last_pos[1]-2, last_pos[1]+2]
        if range_x[0] < 1:
            range_x[0] = 1
        elif range_x[1] > len(self.board[0])-2:
            range_x[1] = len(self.board[0])-2
        x_range = range(range_x[0], range_x[1]+1)

        empty_walls = opponent_walls = my_walls = area_walls = 0
        for i in y_range:
            for j in x_range:
                if (i, j) == last_pos:
                    continue
                if self.board[i][j] == ECell.Empty:
                    empty_walls += 1
                elif self.board[i][j] == my_wall:
                    my_walls += 1
                elif self.board[i][j] == opponent_wall:
                    opponent_walls += 1
                elif self.board[i][j] == ECell.AreaWall:
                    area_walls += 1

        change_ratio = (empty_walls * 8) + (my_walls * -5) + (opponent_walls * -3) + (area_walls * -2)

        change_percentage += (change_ratio/100)

        y_steps = (0, -1, 0, 1)
        x_steps = (-1, 0, 1, 0)
        for i in range(4):
            y = last_pos[0] + y_steps[i]
            x = last_pos[1] + x_steps[i]

            if self.board[i][j] == ECell.Empty:
                empty_walls += 1
            elif self.board[i][j] == my_wall:
                my_walls += 1
            elif self.board[i][j] == opponent_wall:
                opponent_walls += 1

        change_ratio = (empty_walls * 3) + (my_walls * -5) + (opponent_walls * 10)

        change_percentage += (change_ratio/100)

        weight = 100
        weight += weight*(change_percentage)

        route_weights[route] = weight

    routes_weight_sorted = {route: weight for route, weight in sorted(route_weights.items(), key=lambda item: item[1])}

    weights = list(routes_weight_sorted.values())
    max_weight = max(weights)
    max_weight_count = weights.count(max_weight)
    if max_weight_count == 1:
        choosed_route = list(routes_weight_sorted.keys())[-1]
    else:
        max_weight_routes = [route for route in routes_weight_sorted if routes_weight_sorted[route] == max_weight]
        max_weight_routes_sorted = sorted(max_weight_routes, key=lambda route: len(route))
    
        choosed_route = max_weight_routes[-1]

    route_part_1 = choosed_route[0: max_opp_walls]
    self.attacking_all_paths = [route for route in routes if route[0: max_opp_walls] == route_part_1]

    opponent_walls = 0
    for wall_pos in choosed_route:
        y, x = wall_pos[0], wall_pos[1]
        if self.get_wall_type((y, x)) == 'opponent':
            opponent_walls += 1
            if opponent_walls == 6:
                break

    return (choosed_route, opponent_walls)

def update_attacking_path(self):
    print('im here')
    next_index = self.reaching_path_index + 1

    self.log_string += 'attacking all paths before: \n'
    for route in self.attacking_all_paths:
        self.log_string += f'{route}\n'


    delete_after = []
    for route in self.attacking_all_paths:
        remained_part = route[self.reaching_path_index:]
        is_any_wall_non_empty = False
        for wall_pos in remained_part:
            wall_type = self.get_wall_type(wall_pos)

            if wall_type != 'empty':
                is_any_wall_non_empty = True

        if is_any_wall_non_empty:
            delete_after.append(route)

    for route in delete_after:
        self.attacking_all_paths.remove(route)

    self.log_string += 'attacking all paths: \n'
    for route in self.attacking_all_paths:
        self.log_string += f'{route}\n'


    all_next_walls = {route[next_index]: route for route in self.attacking_all_paths}

    route_reached_part = self.attacking_reaching_path[0: self.reaching_path_index + 1]
    
    self.log_string += f'route_reached_part: {route_reached_part}\n'
    
    next_walls = {}
    for wall_pos in all_next_walls:
        if all_next_walls[wall_pos][0: self.reaching_path_index + 1] == route_reached_part:
            next_walls[wall_pos] = all_next_walls[wall_pos]

    all_next_walls = next_walls

    self.log_string += 'all next walls: \n'
    for route in all_next_walls:
        self.log_string += f'{route}\n'

    walls_weights = {wall_pos: self.get_wall_neighbors_weight(wall_pos) for wall_pos in all_next_walls}
    walls_weight_sorted = {wall_pos: weight for wall_pos, weight in sorted(walls_weights.items(), key=lambda item: item[1])}

    min_weight_wall = list(walls_weight_sorted.keys())[0]
    next_best_route = all_next_walls[min_weight_wall]

    self.attacking_reaching_path = next_best_route
    self.target_pos = next_best_route[-1]
            
def find_next_attacking_path(self, start_pos):
    t1 = perf_counter()

    routes = self.find_attack_routes(start_pos)
    if len(routes) == 0 or routes == None:
        self.log_string += 'find next attacking path if_1\n'
        return None

    result_tuple = self.choose_best_attack_route(routes)
    if result_tuple == None:
        self.log_string += 'find next attacking path if_2\n'
        return None

    best_route, opponent_walls = result_tuple[0], result_tuple[1]

    self.attacking_route_opp_walls = opponent_walls

    self.log_string += f'best_route: {best_route}\n'

    t2 = perf_counter()
    time = t2-t1
    self.log_string += f'bfs time: {time}\n'
    return best_route