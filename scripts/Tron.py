from math import sqrt
from ks.models import ECell, EDirection
from time import perf_counter
from random import choice

class Tron:
    def __init__(self):
        self.target_passed_cycles = 0
        self.opponent_distance = 0
        self.attack_target_init_dist = 0
        self.try_again_cycles = 0

        self.agent_state = 'normal' # normal defence attack brutal
        self.agent_attack_state = 'onway' # onway or attacking
        self.around_state = 'normal'
        self.target_wall_type = ''

        self.target_pos = ()
        self.agent_prev_pos = ()

        self.walls = {}
        self.walls_neighbors = {}
        self.walls_awall_neighbors = {}
        self.walls_closest_awall = {}

        self.reaching_path = []
        self.attacking_reaching_path = []
        self.attacking_all_paths = []
        self.best_attack_target_path = []
        self.attacking_route_opp_walls = 0
        self.reaching_path_index = 0

        self.attack_possible_targets = []

        self.log_string = ''

    # class functions import
    from .methods._initialize import set_walls, set_requirements, find_walls_neighbors, find_closest_area_wall
    from .methods._path_finding import find_best_route, find_attack_routes, get_costs, get_heuristics, choose_best_attack_route, find_next_attacking_path, update_attacking_path
    from .methods._target_finding import find_best_wall, find_target, find_route_weight, find_target_handler
    from .methods._minies import is_attack_target_increased, is_target_cycles_exceeded, is_target_reached, is_target_wall_type_changed, is_wallbreaker_needed, \
        show_banner, is_enough_opp_wall_around_us, init_file, output_log, get_distance, is_attack_target_got_unreachable

    def identify_walls(self, check_awalls: bool):
        if self.agent_name == 'Blue':
            m_wall = ECell.BlueWall
            o_wall = ECell.YellowWall
        elif self.agent_name == 'Yellow':
            m_wall = ECell.YellowWall
            o_wall = ECell.BlueWall

        i_range = range(len(self.board))
        for i in i_range:
            j_range = range(len(self.board[i]))
            for j in j_range:
                if self.board[i][j] == m_wall:
                    self.walls['my'].append((i, j))

                elif self.board[i][j] == o_wall:
                    self.walls['opponent'].append((i, j))

                elif self.board[i][j] == ECell.Empty:
                    self.walls['empty'].append((i, j))

                elif self.board[i][j] == ECell.AreaWall:
                    if check_awalls:
                        if i == 0 or i == (len(self.board)-1) or j == 0 or j == (len(self.board[0])-1):
                            self.walls['side_area'].append((i, j))

                        else:
                            y_steps = [0, 1, -1, 0]
                            x_steps = [1, 0, 0, -1]

                            area_wall_sole = False
                            for m in range(4):
                                y = i + y_steps[m]
                                x = j + x_steps[m]
        
                                if self.board[y][x] != ECell.AreaWall:
                                    area_wall_sole = True

                            if area_wall_sole:
                                self.walls['mid_area'].append((i, j))
        
    def get_wall_weight(self, wall_pos):
        wall_y, wall_x = wall_pos[0], wall_pos[1]
        
        opponent_pos = (self.opponent.position.y, self.opponent.position.x)

        if self.agent_pos == (wall_y, wall_x):
            return 10000
        if opponent_pos != (wall_y, wall_x):
            wall_type = self.get_wall_type(wall_pos)

            if self.agent_name == 'Blue':
                my_wall = ECell.BlueWall
                opponent_wall = ECell.YellowWall
            elif self.agent_name == 'Yellow':
                my_wall = ECell.YellowWall
                opponent_wall = ECell.BlueWall

            # calculating distance weight
            agent_distance = self.get_distance(self.agent_pos, wall_pos)
            opponent_distance = self.get_distance(opponent_pos, wall_pos)

            agent_d_ratio = opponent_d_ratio = 1
            if self.board[wall_y][wall_x] == opponent_wall:
                agent_d_ratio = 3

            distance_weight = (agent_distance * agent_d_ratio) + ((1/(opponent_distance)) * opponent_d_ratio)
            distance_weight *= 20
            distance_weight = round(distance_weight)

            weight = distance_weight


            wall_ratio = 1
            # calculating wall itself weight
            if self.agent_state == 'normal' or self.agent_state == 'brutal' or self.agent_state == 'suicide':
                if wall_type == 'my':
                    wall_ratio = 7
                elif wall_type == 'opponent':
                    if self.agent.wall_breaker_cooldown != 0:
                        wall_ratio = 4
                    else:
                        wall_ratio = 3

                elif wall_type == 'empty':
                    wall_ratio = 2

            elif self.agent_state == 'attack':
                if wall_type == 'my':
                    wall_ratio = 7
                elif wall_type == 'opponent':
                    wall_ratio = 2
                    
                elif wall_type == 'empty':
                    wall_ratio = 3
            
            elif self.agent_state == 'defence':
                if wall_type == 'my':
                    wall_ratio = 7
                elif wall_type == 'opponent':
                    if self.agent.wall_breaker_cooldown != 0:
                        wall_ratio = 7
                    else:
                        wall_ratio = 4

                elif wall_type == 'empty':
                    wall_ratio = 2

            weight *= wall_ratio

            value = 1
            ratios = [10, 6, 5, 3]
            for layer in list(self.walls_neighbors[wall_pos].keys())[0:4]:
                my_walls = opponent_walls = empty_walls = area_walls = 0
                walls = self.walls_neighbors[wall_pos][layer] + self.walls_awall_neighbors[wall_pos][layer]

                for wall in walls:
                    wall_type = self.get_wall_type(wall)
                    if wall_type == 'my':
                        my_walls += 1
                    elif wall_type == 'opponent':
                        opponent_walls += 1
                    elif wall_type == 'empty':
                        empty_walls += 1
                    elif wall_type == 'side_area' or 'mid_area':
                        area_walls += 1
            
                empty_walls = 1 if empty_walls == 0 else empty_walls

                change_ratio = (my_walls * ratios[0]) + (opponent_walls * ratios[1]) + ((1 // empty_walls) * ratios[2]) + (area_walls * ratios[3])
                change_ratio *= (10 // value)
                weight += weight*(change_ratio // 100)
                value += 1
                
        else:
            weight = 10000
        
        return round(weight)

    def get_wall_neighbors_weight(self, wall_pos):
        if self.agent_name == 'Blue':
            my_wall = ECell.BlueWall
            opponent_wall = ECell.YellowWall
        elif self.agent_name == 'Yellow':
            my_wall = ECell.YellowWall
            opponent_wall = ECell.BlueWall

        weight = 100
        wall_y, wall_x = wall_pos[0], wall_pos[1]
        my_walls = opponent_walls = empty_walls = area_walls = 0

        y_steps = [1, 0, 0, -1]
        x_steps = [0, 1, -1, 0]
        for i in range(4):
            y = wall_y + y_steps[i]
            x = wall_x + x_steps[i]
            wall_type = self.get_wall_type((y, x))

            if wall_type == 'my':
                my_walls += 1
            elif wall_type == 'opponent':
                opponent_walls += 1
            elif wall_type == 'empty':
                empty_walls += 1
            elif wall_type == 'mid_area' or wall_type == 'side_area':
                area_walls += 1

        if self.board[wall_y][wall_x] == opponent_wall:
            addition_ratios = [5, -10, -20, -15]
            if my_walls == 1:
                addition_ratios[0] = -20
                
            if opponent_walls == 0:
                weight = 1000
            elif opponent_walls == 1:
                addition_ratios[1] = -40
            elif opponent_walls == 3:
                addition_ratios[1] = 0
        
        elif self.board[wall_y][wall_x] == my_wall:
            addition_ratios = [10, -10, -20, -10]

        elif self.board[wall_y][wall_x] == ECell.Empty:
            addition_ratios = [-40, 60, -10, -35]
            if my_walls == 1:
                if empty_walls == 2 or empty_walls == 3:
                    addition_ratios[0] = -60
                if area_walls == 1:
                    addition_ratios[3] = 10
            elif my_walls == 2:
                addition_ratios[0] = -18
            elif my_walls == 3:
                addition_ratios[0] = 0
        
        if my_walls == 2:
            addition_ratios[0] = -10

        if (self.agent_state == 'attack' and self.agent_state == 'attacking') == False:
            if self.agent.wall_breaker_cooldown != 0 and self.agent.wall_breaker_rem_time == 0:
                my_walls = opponent_walls = 0
                addition_ratios = [0, 0, -25, -15]

        weight += (weight*((my_walls * addition_ratios[0])/100))
        weight += (weight*((opponent_walls * addition_ratios[1])/100))
        weight += (weight*((empty_walls * addition_ratios[2])/100))
        weight += (weight*((area_walls * addition_ratios[3])/100))

        return weight

    def update_state(self):
        prev_state = self.agent_state

        opponent_pos = (self.opponent.position.y, self.opponent.position.x)
        distance = round(self.get_distance(self.agent_pos, opponent_pos))
        self.opponent_distance = distance

        my_score, opponent_score = self.scores[self.names[0]], self.scores[self.names[1]]

        if self.agent_state == 'attack' and self.agent_attack_state == 'attacking':
            self.reaching_path_index += 1

            self.log_string += f'{self.reaching_path_index}\n'
            
            if self.reaching_path_index >= len(self.attacking_reaching_path)-1:
                self.agent_state = 'normal'
        
        if self.opponent_distance <= 3:
            if my_score <= opponent_score:
                self.agent_state = 'defence'

            elif my_score > opponent_score + 2:
                if self.opponent_distance <= 2:
                    if self.agent.wall_breaker_cooldown == 0:
                        self.agent_state = 'brutal'
                    
        elif self.agent_state != 'attack':
            if self.opponent_distance <= 5:
                if self.agent.wall_breaker_cooldown == 0:
                    if my_score > opponent_score + 10:
                        self.agent_state = 'brutal'
                    else:
                        self.agent_state = 'attack'

            elif self.opponent_distance >= 4:
                self.agent_state = 'normal'

                if self.curr_cycle >= 20:
                    if self.agent.wall_breaker_cooldown == 0:
                        self.agent_state = 'attack'

        # emergencies
        if (self.agent_state != 'attack') or (self.agent_state == 'attack' and self.agent_attack_state == 'onway'):
            if self.agent.wall_breaker_rem_time == 1:
                self.agent_state = 'normal'

        if self.agent_state == 'defence':
            if distance <= 1:
                self.find_target_handler()

        if my_score + self.area_wall_crash_score - 3 > opponent_score:
            closest_awall = self.walls_closest_awall[self.agent_pos]

            distance = round(self.get_distance(self.agent_pos, closest_awall))
            if distance <= 2:
                self.agent_state = 'suicide'
            else:
                if my_score + self.area_wall_crash_score - 8 > opponent_score:
                    self.agent_state = 'suicide'
        
        self.log_string += f'state:  {self.agent_state} || agent_attack_state:  {self.agent_attack_state}\n'


        if prev_state != self.agent_state:
            self.log_string += f'state changed! {prev_state} => {self.agent_state}\n'
            self.find_target_handler()

    def check_pattern_changing(self):
        curr_empty_walls = 0
        for wall_pos in self.attacking_reaching_path[self.attacking_route_opp_walls:]:
            y, x = wall_pos[0], wall_pos[1]
            if self.board[y][x] == ECell.Empty and (y, x) != self.agent_pos:
                curr_empty_walls += 1

        if self.reaching_path_index < self.attacking_route_opp_walls:
            route_empty_walls = len(self.attacking_reaching_path) - self.attacking_route_opp_walls
        else:
            route_empty_walls = len(self.attacking_reaching_path) - self.reaching_path_index - 1
        
        if curr_empty_walls != route_empty_walls:
            self.log_string += 'pattern changin check if_1 => True\n'
            pattern_changed = True
        else:
            self.log_string += 'pattern changin check else_1 => False\n'

            pattern_changed = False

        last_pos = self.attacking_reaching_path[-1]
        if self.agent_pos == last_pos:
            pattern_changed = False

        if pattern_changed == False and self.reaching_path_index < self.attacking_route_opp_walls:
            if self.agent_attack_state == 'attacking':
                rem_time = self.agent.wall_breaker_rem_time
                if self.agent.wall_breaker_cooldown == 0:
                    rem_time = 6
                
                route_opponent_walls = 0
                for wall_pos in self.attacking_reaching_path[0: self.attacking_route_opp_walls]:
                    wall_type = self.get_wall_type(wall_pos)
                    if wall_type == 'opponent':
                        route_opponent_walls += 1
                
                if rem_time - 1 < route_opponent_walls:
                    self.log_string += 'pattern gonna change, because of if_1\n'
                    pattern_changed = True


        if pattern_changed:
            self.log_string += 'pattern changed\n'

            if self.agent_attack_state == 'attacking':
                if self.reaching_path_index < self.attacking_route_opp_walls:
                    self.log_string += 'state is attacking\n'

                    if self.agent.wall_breaker_rem_time != 0:
                        self.log_string += "rem time wasn't zero\n"
                        next_path = self.find_next_attacking_path(self.agent_pos)

                        if next_path != None:
                            self.log_string += "next path isn't zero, yayyy!\n"

                            self.attacking_reaching_path = next_path
                            self.target_passed_cycles = len(next_path)
                            self.reaching_path_index = 0
                            
                            self.target_pos = next_path[-1]
                            self.target_wall_type = self.get_wall_type(self.target_pos)
                        else:
                            self.log_string += 'next path is zero\n'

                            self.agent_state = 'normal'
                            self.agent_attack_state = 'onway'
                            self.find_target_handler()
                    else:
                        self.log_string += 'rem_time was 0\n'

                        self.agent_state = 'normal'
                        self.agent_attack_state = 'onway'
                        self.find_target_handler()
                else:
                    self.agent_state = 'normal'
                    self.agent_attack_state = 'onway'
                    self.find_target_handler()
            else:
                self.log_string += 'state is onway\n'

                next_path = self.find_next_attacking_path(self.target_pos)

                if next_path != None:
                    self.attacking_reaching_path = next_path
                else:
                    self.agent_state = 'normal'
                    self.agent_attack_state = 'onway'
                    self.find_target_handler()

    def get_wall_type(self, wall_pos):
        if self.agent_name == 'Blue':
            my_wall = ECell.BlueWall
            opponent_wall = ECell.YellowWall
        elif self.agent_name == 'Yellow':
            my_wall = ECell.YellowWall
            opponent_wall = ECell.BlueWall

        pos_y, pos_x = wall_pos[0], wall_pos[1]
        if self.board[pos_y][pos_x] == my_wall:
            return 'my'
        elif self.board[pos_y][pos_x] == opponent_wall:
            return 'opponent'
        elif self.board[pos_y][pos_x] == ECell.Empty:
            return 'empty'
        elif self.board[pos_y][pos_x] == ECell.AreaWall:
            if pos_y == 0 or pos_y == len(self.board)-1 or pos_x == 0 or pos_x == len(self.board[0])-1:
                return 'side_area'
            else:
                return 'mid_area'
            
    def next_dir(self):
        self.agent_prev_pos = self.agent_pos

        next_dir = EDirection.Right
        if self.agent_state != 'attack' or (self.agent_state == 'attack' and self.agent_attack_state == 'onway'):
            index = 1
            next_pos = self.reaching_path[index]
        elif self.agent_state == 'attack' and self.agent_attack_state == 'attacking':
            index = self.reaching_path_index + 1
            next_pos = self.attacking_reaching_path[index]
        
        if self.agent_pos[0] == next_pos[0]:
            if next_pos[1] - self.agent_pos[1] == 1:
                next_dir = EDirection.Right
            else:
                next_dir = EDirection.Left
        else:
            if next_pos[0] - self.agent_pos[0] == 1:
                next_dir = EDirection.Down
            else:
                next_dir = EDirection.Up

        return next_dir

    def show_walls_info(self):
        log_string = ''
        log_string += '{:<5}'.format('*')

        for i in range(len(self.board[0])):
            log_string += '{:<5}'.format(i)
        log_string += '\n'

        for i in range(len(self.board)):
            log_string += '{:<3}  '.format(i)
            for j in range(len(self.board[i])):
                if i == 0 or i == len(self.board)-1:
                    log_string += '{:<5}'.format('====')
                elif j == 0 or j == len(self.board[i])-1:
                    log_string += '{:<5}'.format('||')
                else:
                    opponent_pos = (self.opponent.position.y, self.opponent.position.x)
                    if (i, j) == self.agent_pos:
                        log_string += '{:<5}'.format('M')
                    elif (i, j) == opponent_pos:
                        log_string += '{:<5}'.format('O')
                    elif (i, j) == self.target_pos:
                        log_string += '{:<5}'.format('T')
                    elif self.board[i][j] == ECell.AreaWall:
                        log_string += '{:<5}'.format('+')
                    else:
                        wall_weight = self.get_wall_weight((i, j))
                        log_string += '{:<5}'.format(wall_weight)

            log_string += '\n'
        
        log_string += '\n'

        self.log_string += log_string