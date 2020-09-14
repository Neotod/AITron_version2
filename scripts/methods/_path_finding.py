from ks.models import ECell, EDirection

def get_costs(self, start_pos, dest_pos):
    start_y, end_y = min(start_pos[0], dest_pos[0])-10, max(start_pos[0], dest_pos[0])+10
    start_x, end_x = min(start_pos[1], dest_pos[1])-10, max(start_pos[1], dest_pos[1])+10

    start_y = 1 if start_y < 1 else start_y
    end_y = len(self.board)-2 if end_y > len(self.board)-2 else end_y

    start_x = 1 if start_x < 1 else start_x
    end_x = len(self.board[0])-2 if end_x > len(self.board[0])-2 else end_x

    costs = {}
    for i in range(start_y, end_y+1):
        for j in range(start_x, end_x+1):
            if self.board[i][j] != ECell.AreaWall:
                for wall_type in list(self.walls.keys())[:-2]:
                    positions = list(self.walls[wall_type].keys())
                    position = (i, j)
                    if position in positions:
                        costs[(i, j)] = self.get_wall_weight(position)


        for wall_pos in costs:
            y, x = wall_pos[0], wall_pos[1]

            if self.agent_name == 'Blue':
                m_wall = ECell.BlueWall
                o_wall = ECell.YellowWall
            elif self.agent_name == 'Yellow':
                m_wall = ECell.YellowWall
                o_wall = ECell.BlueWall

            wall_cost = costs[wall_pos]

            if self.agent.wall_breaker_cooldown != 0:
                if self.board[y][x] == o_wall or self.board[y][x] == m_wall:
                    wall_cost += (wall_cost * 40/100)
                    costs[wall_pos] = int(wall_cost)

            if self.board[y][x] == m_wall:
                wall_cost += (wall_cost * 60/100)
                costs[wall_pos] = int(wall_cost)

            # if self.agent_state == 'attack' or self.agent_state == 'brutal':
            #     if self.board[y][x] == o_wall:
            #         if self.agent.wall_breaker_rem_time > 2:
            #             wall_cost -= (wall_cost * 30/100)
            #         else:
            #             wall_cost -= (wall_cost * 10/100)
            #         costs[wall_pos] = int(wall_cost)

            if wall_cost < 0:
                print(f'there is a negative cost here: {wall_pos} | {wall_cost}')

    return costs

def get_heuristics(self, start_pos, dest_pos):
    start_y, end_y = min(start_pos[0], dest_pos[0])-10, max(start_pos[0], dest_pos[0])+10
    start_x, end_x = min(start_pos[1], dest_pos[1])-10, max(start_pos[1], dest_pos[1])+10

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

    return heuristics

def find_best_route(self, start_pos, dest_pos):
    start_y, end_y = min(start_pos[0], dest_pos[0])-10, max(start_pos[0], dest_pos[0])+10
    start_x, end_x = min(start_pos[1], dest_pos[1])-10, max(start_pos[1], dest_pos[1])+10

    start_y = 1 if start_y < 1 else start_y
    end_y = len(self.board)-2 if end_y > len(self.board)-2 else end_y
    
    start_x = 1 if start_x < 1 else start_x
    end_x = len(self.board[0])-2 if end_x > len(self.board[0])-2 else end_x


    heuristics = self.get_heuristics(start_pos, dest_pos)
    costs = self.get_costs(start_pos, dest_pos)

    i, j = start_pos[0], start_pos[1]
    
    open_vertices = {(i, j): [0, []]}
    visited_vertices = {}
    
    cost_so_far = 0
    while True:
        next_node, min_f = (0, 0), 10000000
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
        came_from = open_vertices[current_node][1]
                
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
            if self.board[ii][jj] == ECell.AreaWall:
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

def find_attack_routes(self, target_pos):
    agent_pos = (self.agent.position.y, self.agent.position.x)
    opponnet_pos = (self.opponent.position.y, self.opponent.position.x)

    start_pos = target_pos

    range_y = [start_pos[0]-5, start_pos[0]+5]
    if range_y[0] < 1:
        range_y[0] = 1
    elif range_y[1] > len(self.board)-2:
        range_y[1] = len(self.board)-2
    y_range = range(range_y[0], range_y[1]+1)

    range_x = [start_pos[1]-5, start_pos[1]+5]
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

    routes = [{(start_pos, ): 'open'}]
    while True:
        for route_dict in routes.copy():
            route_itself = list(route_dict.keys())[0]
            route_state = route_dict[route_itself]

            if route_state != 'closed':
                last_pos = route_itself[len(route_itself)-1]

                y_steps = [0, 1, -1, 0]
                x_steps = [1, 0, 0, -1]
                for i in range(4):
                    route_copy = list(route_itself)

                    y = last_pos[0] + y_steps[i]
                    x = last_pos[1] + x_steps[i]
                    
                    if self.board[y][x] == ECell.AreaWall:
                        continue
                    if y not in y_range or x not in x_range:
                        continue
                    if (y, x) in route_copy:
                        continue
                    if (y, x) == opponnet_pos or (y, x) == agent_pos:
                        continue

                    if self.board[y][x] == opponent_wall:
                        if len(route_copy) <= 5:
                            route_copy.append((y, x))
                            new_route_dict = {tuple(route_copy): route_state}
                            routes.append(new_route_dict)
                    
                    elif self.board[y][x] == ECell.Empty or self.board[y][x] == my_wall:
                        if 1 <= len(route_copy) and len(route_copy) <= 6:
                            route_copy.append((y, x))
                            new_route_dict = {tuple(route_copy): 'closed'}

                            routes.append(new_route_dict)

                routes.remove(route_dict)

        opened_routes = 0
        for route_dict in routes:
            route_itself = list(route_dict.keys())[0]
            route_state = route_dict[route_itself]
            
            if route_state == 'open':
                opened_routes += 1
        if opened_routes == 0:
            break
    
    closed_routes = []
    for route_dict in routes:
        route_itself = list(route_dict.keys())[0]
        route_state = route_dict[route_itself]
        closed_routes.append(route_itself)

    return closed_routes

def choose_best_attack_route(self, routes):
    if self.agent_name == 'Blue':
        my_wall = ECell.BlueWall
        opponent_wall = ECell.YellowWall
    elif self.agent_name == 'Yellow':
        my_wall = ECell.YellowWall
        opponent_wall = ECell.BlueWall

    
    wall_breaker_rem_time = self.agent.wall_breaker_rem_time+1
    if self.agent.wall_breaker_cooldown == 0:
        wall_breaker_rem_time = 6

    correct_routes = [route for route in routes if len(route) <= wall_breaker_rem_time]
    routes = correct_routes


    routes_weights = []
    for route in routes:
        opponent_walls = my_walls = 0
        for wall_pos in route:
            wall_y, wall_x = wall_pos[0], wall_pos[1]
        
            if self.board[wall_y][wall_x] == opponent_wall:
                opponent_walls += 1
            elif self.board[wall_y][wall_x] == my_wall:
                my_walls += 1

        change_percentage = -(opponent_walls*12/100) + (my_walls*40/100)

        last_pos = route[len(route)-1]

        range_y = [last_pos[0]-3, last_pos[0]+3]
        if range_y[0] < 1:
            range_y[0] = 1
        elif range_y[1] > len(self.board)-2:
            range_y[1] = len(self.board)-2
        y_range = range(range_y[0], range_y[1]+1)

        range_x = [last_pos[1]-3, last_pos[1]+3]
        if range_x[0] < 1:
            range_x[0] = 1
        elif range_x[1] > len(self.board[0])-2:
            range_x[1] = len(self.board[0])-2
        x_range = range(range_x[0], range_x[1]+1)

        empty_walls = opponent_walls = my_walls = 0
        for i in y_range:
            for j in x_range:
                if self.board[i][j] == ECell.Empty:
                    empty_walls += 1
                elif self.board[i][j] == my_wall:
                    my_walls += 1
                elif self.board[i][j] == opponent_wall:
                    opponent_walls += 1

        change_ratio = (empty_walls * -0.5) + (my_walls * 7) + (opponent_walls * 3)
        change_percentage += (change_ratio/100)

        weight = 250
        weight += weight*(change_percentage)

        routes_weights.append(weight)

    for i in range(len(routes)):
        print(f'{routes[i]}  ||  {routes_weights[i]}')


    min_weight = min(routes_weights)
    min_weight_count = routes_weights.count(min_weight)
    if min_weight_count == 1:
        index = routes_weights.index(min_weight)
    else:
        min_weight_routes = []
        start = 0
        for i in range(min_weight_count):
            index = routes_weights[start:].index(min_weight)
            min_weight_routes.append(routes[index])

            start = index
            start += 1
        
        len_of_routes = [len(route) for route in min_weight_routes]
        max_len = max(len_of_routes)
        len_index = len_of_routes.index(max_len)

        route = min_weight_routes[len_index]
        index = routes.index(route)


    return routes[index]

def set_next_route(self):
    if self.agent_state != 'attack' or (self.agent_state == 'attack' and self.agent_attack_state == 'onway'):
        agent_pos = (self.agent.position.y, self.agent.position.x)
        best_route = self.find_best_route(agent_pos, self.target_pos)

        self.reaching_path = best_route

    elif self.agent_state == 'attack' and self.agent_attack_state == 'attacking':
        if self.reaching_path_index == -1:
            routes = self.find_attack_routes(self.target_pos)
            best_route = self.choose_best_attack_route(routes)
            print('best_route: ', best_route)
            
            last_pos = best_route[len(best_route)-1]
            self.target_pos = last_pos

            self.reaching_path = best_route
            self.reaching_path_index = 0