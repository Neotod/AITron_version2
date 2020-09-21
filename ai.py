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
        self.tron.find_walls_info()
        
        self.tron.find_target_handler()

    def decide(self):
        time_sum = 0

        agents = self.world.agents
        names = [self.my_side, self.other_side]
        scores = self.world.scores
        board = self.world.board
        curr_cycle = self.current_cycle
        crash_score = self.world.constants.area_wall_crash_score
        self.tron.set_requirements(agents, names, scores, board, curr_cycle, crash_score)


        self.tron.log_string += f'cycle: {self.current_cycle}\n'
        self.tron.log_string += f'current_position: {(agents[self.my_side].position.y, agents[self.my_side].position.x)}\n'
        

        t1 = perf_counter()
        self.tron.set_walls()
        self.tron.identify_walls(False)

        t2 = perf_counter()
        time_sum += (t2-t1)
        # print('identify walls: {:.5f}'.format(t2-t1))


        t1 = perf_counter()
        
        self.tron.find_walls_info()

        t2 = perf_counter()
        time_sum += (t2-t1)
        # print('find_walls_info: {:.5f}'.format(t2-t1))


        t1 = perf_counter()

        self.tron.update_state()

        t2 = perf_counter()
        time_sum += (t2-t1)
        # print('update_state: {:.5f}'.format(t2-t1))
        

        t1 = perf_counter()

        self.tron.find_walls_info()

        t2 = perf_counter()
        time_sum += (t2-t1)
        # print('find_walls_info: {:.5f}'.format(t2-t1))


        t1 = perf_counter()
        
        if self.tron.is_target_reached():
            if self.tron.agent_state == 'attack':
                if self.tron.agent_attack_state == 'attacking':
                    self.tron.find_target_handler()
                else:
                    self.tron.agent_attack_state = 'attacking'
                    self.tron.reaching_path_index = -1

            else:
                self.tron.find_target_handler()
            
        elif self.tron.is_target_cycles_exceeded() or self.tron.agent_state == 'brutal':
            self.tron.find_target_handler()

        elif self.tron.is_target_wall_type_changed():
            self.tron.find_target_handler()

        if self.tron.agent_state == 'attack' and self.tron.agent_attack_state == 'onway':
            if self.tron.is_attack_target_increased():


                self.tron.log_string += 'increased!\n'


                self.tron.find_target_handler()

        t2 = perf_counter()
        time_sum += (t2-t1)
        # print('find_target: {:.5f}'.format(t2-t1))


        t1 = perf_counter()

        self.tron.set_next_route()

        t2 = perf_counter()
        time_sum += (t2-t1)
        # print('find_next_route {:.5f}'.format(t2-t1))


        t1 = perf_counter()

        if self.tron.agent_state != 'suicide':
            target_weight = self.tron.get_wall_weight(self.tron.target_pos)
        else:
            target_weight = 0


        self.tron.log_string += f'target: {self.tron.target_pos} weight: {target_weight}\n\n'


        self.tron.show_walls_info()

        t2 = perf_counter()
        time_sum += (t2-t1)


        self.tron.log_string += 'showing things {:.5f}\n'.format(t2-t1)
        

        if self.tron.is_wallbreaker_needed():
            if agents[self.my_side].wall_breaker_cooldown == 0:
                self.send_command(ActivateWallBreaker())

        next_dir = self.tron.next_dir()
        self.send_command(ChangeDirection(next_dir))

    
        self.tron.log_string += 'overall_time: {:.5f}\n\n\n\n'.format(time_sum)
        t1 = perf_counter()
        self.tron.output_log()
        t2 = perf_counter()
        print('log time: {:.5f}\n'.format(t2-t1))
