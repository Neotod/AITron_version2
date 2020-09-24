# -*- coding: utf-8 -*-

# python imports
import random

# chillin imports
from chillin_client import RealtimeAI

# project imports
from ks.models import ECell, EDirection, Position
from ks.commands import ChangeDirection, ActivateWallBreaker

from scripts.Tron import Tron

from time import perf_counter


class AI(RealtimeAI):

    def __init__(self, world):
        super(AI, self).__init__(world)


    def initialize(self):
        self.tron = Tron()
        self.tron.set_walls()
        self.tron.show_banner()

        agents = self.world.agents
        names = [self.my_side, self.other_side]
        scores = self.world.scores
        board = self.world.board
        curr_cycle = self.current_cycle
        crash_score = self.world.constants.area_wall_crash_score
        self.tron.set_requirements(agents, names, scores, board, curr_cycle, crash_score)

        self.tron.init_file()

        self.tron.identify_walls(True)
        self.tron.find_walls_neighbors()
        self.tron.find_closest_area_wall()
        
        self.tron.find_target_handler()

    def decide(self):
        tt1 = perf_counter()

        agents = self.world.agents
        names = [self.my_side, self.other_side]
        scores = self.world.scores
        board = self.world.board
        curr_cycle = self.current_cycle
        crash_score = self.world.constants.area_wall_crash_score
        self.tron.set_requirements(agents, names, scores, board, curr_cycle, crash_score)


        self.tron.log_string += f'cycle: {self.current_cycle}\n'

        print(f'cycle: {self.current_cycle}')

        self.tron.log_string += f'current_position: {(agents[self.my_side].position.y, agents[self.my_side].position.x)}\n'

        t1 = perf_counter()
        self.tron.set_walls()
        self.tron.identify_walls(False)
        t2 = perf_counter()
        print('identify walls: {:.5f}'.format(t2-t1))

        t1 = perf_counter()
        self.tron.update_state()
        t2 = perf_counter()
        print('update_state: {:.5f}'.format(t2-t1))
        
        t1 = perf_counter()
        if self.tron.is_target_reached():
            self.tron.log_string += 'target reached!\n'

            if self.tron.agent_state == 'attack':
                self.tron.log_string += "target reached! state is attack\n"

                if self.tron.agent_attack_state == 'onway':
                    self.tron.agent_attack_state = 'attacking'
                    self.target_passed_cycles = len(self.tron.attacking_reaching_path)
                    
                    self.tron.target_pos = self.tron.attacking_reaching_path[-1]
                    self.tron.target_wall_type = self.tron.get_wall_type(self.tron.target_pos)
                    
                    self.tron.try_again_cycles = 0
                else:
                    self.tron.agent_attack_state = 'onway'
                    self.tron.reaching_path_index = 0
                    self.tron.find_target_handler()

            else:
                self.tron.log_string += "target reached! state isn't attack!\n"
                self.tron.find_target_handler()
            
        elif self.tron.is_target_cycles_exceeded() or self.tron.agent_state == 'brutal':
            self.tron.log_string += 'target cycles_exceeded!\n'
            self.tron.find_target_handler()

        elif self.tron.is_target_wall_type_changed():
            self.tron.log_string += 'wall_type_changedd!\n'
            self.tron.find_target_handler()

        if self.tron.agent_state == 'attack' and self.tron.agent_attack_state == 'onway':
            if self.tron.is_attack_target_increased():
                self.tron.log_string += 'increased!\n'
                self.tron.find_target_handler()
            
            elif self.tron.try_again_cycles == 0:
                if self.tron.is_attack_target_got_unreachable():
                    self.tron.log_string += 'attack target got unreachable\n'
                    self.tron.find_target_handler()

        t2 = perf_counter()
        # print('find_target: {:.5f}'.format(t2-t1))
        if self.tron.agent_state == 'attack':
            self.tron.check_pattern_changing()
            if self.tron.agent_attack_state == 'attacking':
                if self.tron.reaching_path_index >= self.tron.attacking_route_opp_walls - 1:
                    self.tron.update_attacking_path()


        if self.tron.agent_state != 'attack' or (self.tron.agent_state == 'attack' and self.tron.agent_attack_state == 'onway'):
            t1 = perf_counter()
            ignore_cost = False
            if self.tron.try_again_cycles != 0:
                ignore_cost = True

            agent_pos = (self.tron.agent.position.y, self.tron.agent.position.x)
            best_route = self.tron.find_best_route(agent_pos, self.tron.target_pos, ignore_cost)
            self.tron.reaching_path = best_route

            if self.tron.agent_state == 'attack' and self.tron.agent_attack_state == 'onway':
                self.tron.best_attack_target_path = best_route
                    
            t2 = perf_counter()
            print('find_next_route {:.5f}'.format(t2-t1))


        t1 = perf_counter()
        if self.tron.agent_state != 'suicide':
            target_weight = self.tron.get_wall_weight(self.tron.target_pos)
        else:
            target_weight = 0

        # self.tron.log_string += f'target: {self.tron.target_pos} weight: {target_weight}\n\n'

        # self.tron.show_walls_info()
        t2 = perf_counter()

        # self.tron.log_string += 'showing things {:.5f}\n'.format(t2-t1)
        

        if self.tron.is_wallbreaker_needed():
            if agents[self.my_side].wall_breaker_cooldown == 0:
                self.send_command(ActivateWallBreaker())

        next_dir = self.tron.next_dir()
        self.send_command(ChangeDirection(next_dir))

        # t1 = perf_counter()
        # self.tron.output_log()
        # t2 = perf_counter()
        # print('log time: {:.5f}'.format(t2-t1))


        tt2 = perf_counter()
        overall_time = tt2-tt1
        # self.tron.log_string += 'overall_time: {:.5f}\n\n\n'.format(overall_time)
        print('overall_time: {:.5f}\n\n\n'.format(overall_time))