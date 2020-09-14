def find_target(self):
    if self.agent_state == 'normal':
        agent_y, agent_x = self.agent.position.y, self.agent.position.x
        curr_wall_neighbors = self.walls_neighbors[(agent_y, agent_x)]

        wall_pos = self.find_best_wall(curr_wall_neighbors)

    elif self.agent_state == 'attack':
        opponent_walls = list(self.walls['opponent'].keys()).copy()

        agent_pos = (self.agent.position.y, self.agent.position.x)
        if agent_pos in opponent_walls:
            print('yeah, agent is here')
            opponent_walls.remove(agent_pos)
        
        opponent_pos = (self.opponent.position.y, self.opponent.position.x)
        if opponent_pos in opponent_walls:
            print('yeah, opponent is here')
            opponent_walls.remove(opponent_pos)

        self.agent_attack_state = 'onway'

        wall_pos = self.find_best_wall(opponent_walls)

    elif self.agent_state == 'defence':
        opponent_y, opponent_x = self.opponent.position.y, self.opponent.position.x

        range_y1 = opponent_y-2
        range_y2 = opponent_y+2
        if range_y1 <= 1:
            range_y1 = 1
        elif range_y2 >= len(self.board)-2:
            range_y2 = len(self.board)
            
        range_y = range(range_y1, range_y2+1)
        
        range_x1 = opponent_x-2
        range_x2 = opponent_x+2
        if range_x1 <= 1:
            range_x1 = 1
        elif range_x2 >= len(self.board[0])-2:
            range_x2 = len(self.board[0])

        range_x = range(range_x1, range_x2+1)

        agent_y, agent_x = self.agent.position.y, self.agent.position.x
        curr_wall_neighbors = self.walls_neighbors[(agent_y, agent_x)]

        qual_neighbor_walls = [position for position in curr_wall_neighbors if position[0] not in range_y and position[1] not in range_x]

        neighbors_weights = [self.get_wall_weight(position) for position in qual_neighbor_walls]

        min_weight = min(neighbors_weights)
        weight_index = neighbors_weights.index(min_weight)
        neighbor_pos = qual_neighbor_walls[weight_index]
        
        wall_pos = neighbor_pos

    elif self.agent_state == 'brutal':
        opponent_pos = (self.opponent.position.y, self.opponent.position.x)
        wall_pos = opponent_pos

    print(f'target changed => {wall_pos}')
    self.target_passed_cycles = 10
    self.target_pos = wall_pos

def find_best_wall(self, walls):
    if self.agent_state == 'normal':
        qualified_targets = []

        walls_weights = [self.get_wall_weight(wall_pos) for wall_pos in walls]
        min_weight = min(walls_weights)
        
        walls_to_remove = []
        for i in range(len(walls)):
            weight = walls_weights[i]
            diff = abs(weight - min_weight)

            accepted_range = range(0, 101)
            if diff not in accepted_range:
                walls_to_remove.append(walls[i])

        for wall_pos in walls_to_remove:
            walls.remove(wall_pos)


        walls_weights = [self.get_wall_weight(wall_pos) for wall_pos in walls]
        min_weight = min(walls_weights)
        index = walls_weights.index(min_weight)

        qualified_targets.append(walls[index])
        walls.pop(index)
        
        walls_agent_d = [self.walls[self.get_wall_type(wall_pos)][wall_pos]['agent_d'] for wall_pos in walls]
        min_distance = min(walls_agent_d)
        index1 = walls_agent_d.index(min_distance)

        max_distance = max(walls_agent_d)
        index2 = walls_agent_d.index(max_distance)

        qualified_targets.append(walls[index1])
        qualified_targets.append(walls[index2])

        targets_route = {}
        for target in qualified_targets:
            agent_pos = (self.agent.position.y, self.agent.position.x)
            route = self.find_best_route(agent_pos, target)

            targets_route[target] = route

        best_target = self.choose_best_target(targets_route)
        wall_pos = best_target

        return wall_pos
    
    elif self.agent_state == 'attack':
        walls_weights = [self.get_wall_weight(wall_pos) for wall_pos in walls]
        average = sum(walls_weights) // len(walls_weights)
        min_weight = min(walls_weights)
        weight_range = (min_weight, average+1)

        choosed_walls = []
        for i in range(len(walls)):
            weight = walls_weights[i]
            if weight in weight_range:
                choosed_walls.append(walls[i])
            
        distances_from_agent = [self.walls[self.get_wall_type(wall_pos)][wall_pos]['agent_d'] for wall_pos in choosed_walls]
        min_distance = min(distances_from_agent)
        index = distances_from_agent.index(min_distance)


        # index = walls_weights.index(min_weight)
        wall_pos = choosed_walls[index]

        return wall_pos

def choose_best_target(self, routes):
    opponent_walls = my_walls = empty_walls = 0
    routes_weight = {}
    print(routes)
    for target in routes:
        weight = 100
        route = routes[target]

        for wall_pos in route:
            wall_type = self.get_wall_type(wall_pos)

            if wall_type == 'opponent':
                opponent_walls += 1
            elif wall_type == 'my':
                my_walls += 1
            elif wall_type == 'empty':
                empty_walls += 1
        
        ratios = [5, 20, -3]
        if self.agent_state == 'normal':
            ratios[0] = 70
            ratios[1] = 80
            if self.agent.wall_breaker_cooldown != 0:
                ratios[0] = 90
                ratios[1] = 90

        # elif self.agent_state == 'attack':
        #     ratios[0] = 5
        #     ratios[1] += 60
        
        
        change_percentage = (opponent_walls * ratios[0]) + (my_walls * ratios[1]) + (empty_walls * ratios[2])
        weight += weight*(change_percentage/100)

        routes_weight[target] = weight
    
    print(routes_weight)

    min_weight = min(list(routes_weight.values()))
    min_weight_count = list(routes_weight.values()).count(min_weight)
    if min_weight_count == 1:
        index = list(routes_weight.values()).index(min_weight)
        target = list(routes.keys())[index]

    else:
        same_weight_targets = []
        for target in routes_weight:
            weight = routes_weight[target]
            if weight == min_weight:
                same_weight_targets.append(target)

        targets_weights = [self.get_wall_weight(target) for target in same_weight_targets]
        min_weight = min(targets_weights)

        index = targets_weights.index(min_weight)
        target = same_weight_targets[index]

    
    return target