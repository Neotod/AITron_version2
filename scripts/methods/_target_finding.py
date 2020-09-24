from ks.models import ECell
from time import perf_counter

def find_target(self):
    log_string = ''
    if self.agent_state == 'normal':
        t1 = perf_counter()

        all_neighbors = self.walls_neighbors[self.agent_pos]
        if (self.agent.wall_breaker_cooldown != 0 and self.agent.wall_breaker_rem_time == 0):
            neighbor_walls = all_neighbors[1]

            if self.agent_prev_pos in neighbor_walls:
                neighbor_walls.remove(self.agent_prev_pos)
            
            neighbor_walls_types = [self.get_wall_type(wall_pos) for wall_pos in neighbor_walls]
            is_any_empty_wall = False
            for wall_type in neighbor_walls_types:
                if wall_type == 'empty':
                    is_any_empty_wall = True
                    break
            
            if is_any_empty_wall == False:
                layer2_walls = all_neighbors[1] + all_neighbors[2]
                neighbor_walls = neighbor_walls + layer2_walls

            walls_and_weights = {wall: self.get_wall_weight(wall) for wall in neighbor_walls if wall != self.agent_prev_pos}
            walls_and_weights_sorted = {k: v for k, v in sorted(walls_and_weights.items(), key=lambda item: item[1])}

            choosed_walls = {wall: walls_and_weights_sorted[wall] for wall in list(walls_and_weights_sorted.keys())[0:5]}

        else:
            choosed_walls = {}
            if self.reaching_path_index == -1:
                all_neighbors = {layer: all_neighbors[layer] for layer in list(all_neighbors.keys())[0:3]}
                
            for layer in all_neighbors:
                neighbor_walls = all_neighbors[layer]

                walls_and_weights = {wall: self.get_wall_weight(wall) for wall in neighbor_walls}
                walls_and_weights_sorted = {k: v for k, v in sorted(walls_and_weights.items(), key=lambda item: item[1])}

                log_string += f'layer {layer}, raw_weights: {walls_and_weights_sorted}\n'

                wall = list(walls_and_weights_sorted.keys())[0]
                if wall == self.agent_prev_pos:
                    wall = list(walls_and_weights_sorted.keys())[1]
                    
                choosed_walls[wall] = walls_and_weights[wall]

        log_string += f'all walls: {choosed_walls}\n'
        self.log_string += log_string

        wall_pos = self.find_best_wall(choosed_walls)


        t2 = perf_counter()
        time = t2-t1
        self.log_string += 'find_best_wall__normal_time: {:.5f}\n'.format(time)

    elif self.agent_state == 'attack':
        t1 = perf_counter()

        range_y = [self.agent_pos[0]-6, self.agent_pos[0]+6]
        range_y[0] = 1 if range_y[0] < 1 else range_y[0]
        range_y[1] = len(self.board)-2 if range_y[1] > len(self.board)-2 else range_y[1]
        y_range = range(range_y[0], range_y[1]+1)

        range_x = [self.agent_pos[1]-9, self.agent_pos[1]+9]
        range_x[0] = 1 if range_x[0] < 1 else range_x[0]
        range_x[1] = len(self.board[0])-2 if range_x[1] > len(self.board[0])-2 else range_x[1]
        x_range = range(range_x[0], range_x[1]+1)

        last_x_range = last_y_range = range(-1, -5)
        walls_number = 0
        opponent_walls = []
        for l in range(3):
            for i in y_range:
                if i not in last_y_range:
                    for j in x_range:
                        if j not in last_x_range:
                            wall_type = self.get_wall_type((i, j))
                            if wall_type == 'opponent':
                                walls_number += 1
                                opponent_walls.append((i, j))
                                    
            if len(opponent_walls) >= 5:
                break

            last_y_range = y_range
            range_y[0] -= 2
            range_y[1] += 2
            range_y[0] = 1 if range_y[0] < 1 else range_y[0]
            range_y[1] = len(self.board)-2 if range_y[1] > len(self.board)-2 else range_y[1]
            y_range = range(round(range_y[0]), round(range_y[1]+1))
            
            last_x_range = x_range
            range_x[0] -= 3.5
            range_x[1] += 3.5
            range_x[0] = 1 if range_x[0] < 1 else range_x[0]
            range_x[1] = len(self.board[0])-2 if range_x[1] > len(self.board[0])-2 else range_x[1]
            x_range = range(round(range_x[0]), round(range_x[1]+1))

        self.agent_attack_state = 'onway'
        if len(opponent_walls) == 0:
            return None

        wall_pos = self.find_best_wall(opponent_walls)
        if wall_pos == None:
            print('end of attack finding target, find best wall returned NONE')

            return None

        distance_from_agent = self.get_distance(self.agent_pos, wall_pos)
        self.attack_target_init_dist = distance_from_agent

        
        t2 = perf_counter()
        time = t2-t1
        self.log_string += 'find_best_wall__attack_time: {:5f}\n'.format(time)
        
        print('end of attack finding target')

    elif self.agent_state == 'defence':
        opponent_y, opponent_x = self.opponent.position.y, self.opponent.position.x

        range_y1 = opponent_y-2
        range_y2 = opponent_y+2
        if range_y1 <= 1:
            range_y1 = 1
        elif range_y2 >= len(self.board)-2:
            range_y2 = len(self.board)-2
            
        range_y = range(range_y1, range_y2+1)
        
        range_x1 = opponent_x-4
        range_x2 = opponent_x+4
        if range_x1 <= 1:
            range_x1 = 1
        elif range_x2 >= len(self.board[0])-2:
            range_x2 = len(self.board[0])-2

        range_x = range(range_x1, range_x2+1)

        curr_wall_neighbors = [wall for layer in self.walls_neighbors[self.agent_pos].keys() for wall in self.walls_neighbors[self.agent_pos][layer]]

        qual_neighbor_walls = [position for position in curr_wall_neighbors if (position[0] not in range_y) and (position[1] not in range_x)]

        neighbors_weights = [self.get_wall_weight(position) for position in qual_neighbor_walls]

        min_weight = min(neighbors_weights)
        weight_index = neighbors_weights.index(min_weight)
        neighbor_pos = qual_neighbor_walls[weight_index]
        
        wall_pos = neighbor_pos

    elif self.agent_state == 'brutal':
        opponent_pos = (self.opponent.position.y, self.opponent.position.x)
        wall_pos = opponent_pos
    
    elif self.agent_state == 'suicide':
        closest_awall_pos = self.walls_closest_awall[self.agent_pos]

        wall_pos = closest_awall_pos

    return wall_pos

def find_best_wall(self, walls):
    log_string = ''
    if self.agent_state == 'normal':
        walls_and_weights = walls # because in normal state we sent wall+wall's weight to this method

        walls_and_weights = {wall_pos: self.get_wall_neighbors_weight(wall_pos) + walls_and_weights[wall_pos] for wall_pos in walls_and_weights}
        walls_and_weights_sorted = {k: v for k, v in sorted(walls_and_weights.items(), key=lambda item: item[1])}

        log_string += 'walls: \n'
        for wall_pos in walls_and_weights_sorted:
            weight_1 = self.get_wall_neighbors_weight(wall_pos)
            weight_2 = self.get_wall_weight(wall_pos)
            log_string += f'{wall_pos}: {weight_1} + {weight_2}     '
        log_string += '\n'

        qualified_targets = {k: walls_and_weights_sorted[k] for k in list(walls_and_weights_sorted.keys())[0:3]}

        t1 = perf_counter()
        targets_route = {}
        for target in qualified_targets:
            route = self.find_best_route(self.agent_pos, target)

            targets_route[target] = route
        t2 = perf_counter()
        time = t2-t1
        self.log_string += 'normal A star time: {:.5f}\n'.format(time)

        targets_route_weight = {target: self.find_route_weight(route) for target, route in targets_route.items()}
        
        weights = list(targets_route_weight.values())
        min_weight = min(weights)
        min_weight_count = weights.count(min_weight)
        if min_weight_count == 1:
            index = weights.index(min_weight)
            best_target = list(targets_route_weight.keys())[index]

        else:
            same_weight_targets = []
            for target in targets_route_weight:
                weight = targets_route_weight[target]
                if weight == min_weight:
                    same_weight_targets.append(target)

            targets_distances = [self.get_distance(self.agent_pos, target) for target in same_weight_targets]
            min_distance = min(targets_distances)

            index = targets_distances.index(min_distance)
            best_target = same_weight_targets[index]

        wall_pos = best_target

    elif self.agent_state == 'attack':
        walls_weights = {wall_pos: self.get_wall_weight(wall_pos) for wall_pos in walls}
        walls_weights_sorted = {k: v for k, v in sorted(walls_weights.items(), key=lambda item: item[1])}
        
        log_string += 'walls raw weights: \n'
        for wall in walls_weights_sorted:
            log_string += f'{wall}: {walls_weights[wall]},    '
        log_string += '\n'

        
        weights = list(walls_weights_sorted.values())
        min_weight = round(min(weights))
        average = int((min_weight + max(weights)) // 2)
        acceptance_range = range(min_weight, average+1)

        choosed_walls = [wall_pos for wall_pos in walls_weights_sorted.keys() if round(walls_weights_sorted[wall_pos]) in acceptance_range]

        log_string += f'choosed_walls: {choosed_walls}\n'

        walls_neighbor_weights = {wall_pos: self.get_wall_neighbors_weight(wall_pos) for wall_pos in choosed_walls}
        # check if any opponent wall doesn't have any other opponent neighbor and then remove it
        walls_neighbor_weights = {wall_pos: walls_neighbor_weights[wall_pos] for wall_pos in walls_neighbor_weights if walls_neighbor_weights[wall_pos] != 1000}

        log_string += f'walls_neighbor_weights: {walls_neighbor_weights}\n'

        walls_distances = {wall_pos: self.get_distance(self.agent_pos, wall_pos) * 10 for wall_pos in walls_neighbor_weights}

        log_string += f'walls_distances: {walls_distances}\n'

        walls_and_sums = {wall_pos: walls_neighbor_weights[wall_pos] + walls_distances[wall_pos] for wall_pos in walls_distances}

        log_string += f'walls_and_sums: {walls_and_sums}\n'

        walls_and_sums_sorted = {k: v for k, v in sorted(list(walls_and_sums.items()), key=lambda item: item[1])}
        choosed_walls = list(walls_and_sums_sorted.keys())[0:3]

        log_string += f'final choosed_walls: {choosed_walls}\n'

        t1 = perf_counter()
        targets_route = {}
        for target in choosed_walls:
            route = self.find_best_route(self.agent_pos, target, ignore_cost=True)

            targets_route[target] = route
        
        t2 = perf_counter()

        log_string += 'A star time: {:.5f}\n'.format(t2-t1)
        

        targets_route_weight = {target: self.find_route_weight(route) for target, route in targets_route.items()}

        log_string += f'targets_route: \n'
        for target in targets_route:
            route = targets_route[target]

            log_string += f'{target}: {route} => {targets_route_weight[target]}\n'
            

        # check if any of the targets are behind one of my own or opponent walls and then remove them
        acceptable_targets = {target: targets_route_weight[target] for target in targets_route_weight if targets_route_weight[target] == 100}

        # if all of the targets are behind one of my own or opponent walls, so it's ok :)
        if len(acceptable_targets) == 0:
            # there is no good target for attacking try again
            self.log_string += f'try agian cycles: {self.try_again_cycles}\n'

            self.try_again_cycles += 1
            if self.try_again_cycles < 10:
                return None
            else:
                self.log_string += f'try agian cycles exceeded!\n'
                acceptable_targets = targets_route_weight


        weights = list(acceptable_targets.values())
        min_weight = min(weights)
        min_weight_count = weights.count(min_weight)
        if min_weight_count == 1:
            index = weights.index(min_weight)
            best_target = list(acceptable_targets.keys())[index]
        else:
            same_weight_targets = []
            for target in acceptable_targets:
                weight = acceptable_targets[target]
                if weight == min_weight:
                    same_weight_targets.append(target)

            targets_distances = [self.get_distance(self.agent_pos, target) for target in same_weight_targets]
            min_distance = min(targets_distances)

            index = targets_distances.index(min_distance)
            best_target = same_weight_targets[index]

        self.best_attack_target_path = targets_route[best_target]
        wall_pos = best_target    

    self.log_string += log_string


    return wall_pos

def find_route_weight(self, route):
    weight = 100
    opponent_walls = my_walls = empty_walls = 0

    for wall_pos in route:
        wall_type = self.get_wall_type(wall_pos)

        if wall_type == 'opponent':
            opponent_walls += 1
        elif wall_type == 'my':
            my_walls += 1
        elif wall_type == 'empty':
            empty_walls += 1
    
    ratios = [10, 20, -1]
    if self.agent_state == 'normal':
        ratios[0] = 70
        ratios[1] = 80
        if self.agent.wall_breaker_cooldown != 0 and self.agent.wall_breaker_rem_time == 0:
            ratios[0] = 90
            ratios[1] = 90
    else:
        ratios = [1, 1, 0]
        opponent_walls -= 1
        empty_walls = 0
    
    change_percentage = (opponent_walls * ratios[0]) + (my_walls * ratios[1]) + (empty_walls + ratios[2])
    weight += weight*(change_percentage/100)
    
    return weight

def find_target_handler(self):
    self.log_string += 'inside target handler\n'
    t1 = perf_counter()

    log_string = ''

    wall_pos = self.find_target()
    if self.agent_state == 'attack':
        if wall_pos == None:
            self.log_string += 'find target handler, if_1\n'

            log_string += "there wasn't any acceptable attack target so WE WON'T ATTACK!\n"
            self.reaching_path_index = -1
            self.agent_state = 'normal'
            wall_pos = self.find_target()
        else:
            self.log_string += 'find target handler, else_1\n'

            self.log_string += f'selected target: {wall_pos}\n'

            next_path = self.find_next_attacking_path(wall_pos)
            if next_path != None:
                self.log_string += 'find target handler, if_2\n'

                self.attacking_reaching_path = next_path
            else:
                self.log_string += 'find target handler, else_2\n'

                log_string += "there wasn't any acceptable route to attack target so WE WON'T ATTACK!\n"
                self.reaching_path_index = -1
                self.agent_state = 'normal'
                wall_pos = self.find_target()

    self.reaching_path_index = 0
    self.target_passed_cycles = 10
    self.target_pos = wall_pos
    self.target_wall_type = self.get_wall_type(self.target_pos)

    log_string += f'\ttarget changed => {wall_pos} || type: {self.target_wall_type}\n'
    self.log_string += log_string

    t2 = perf_counter()
    print('find_target: {:.5f}'.format(t2-t1))