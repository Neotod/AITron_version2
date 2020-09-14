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
        t1 = perf_counter()

        self.tron = Tron()
        self.tron.set_walls()
        # self.tron.show_banner()

        agents = self.world.agents
        names = [self.my_side, self.other_side]
        scores = self.world.scores
        board = self.world.board
        curr_cycle = self.current_cycle
        self.tron.set_requirements(agents, names, scores, board, curr_cycle)
    
        self.tron.identify_walls(True)
        self.tron.find_walls_neighbors()
        self.tron.find_closest_area_wall()
        self.tron.find_walls_info()
        
        self.tron.find_target()

        t2 = perf_counter()

        print('initialize time: {:.5f}'.format(t2-t1))

    def decide(self):
        time_sum = 0

        agents = self.world.agents
        names = [self.my_side, self.other_side]
        scores = self.world.scores
        board = self.world.board
        curr_cycle = self.current_cycle
        self.tron.set_requirements(agents, names, scores, board, curr_cycle)


        t1 = perf_counter()

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
                    self.tron.find_target()
                else:
                    self.tron.agent_attack_state = 'attacking'
                    self.tron.reaching_path_index = -1

            else:
                self.tron.find_target()
            
        if self.tron.is_target_cycles_exceeded():
            self.tron.find_target()

        t2 = perf_counter()
        time_sum += (t2-t1)
        # print('find_target: {:.5f}'.format(t2-t1))


        t1 = perf_counter()

        self.tron.set_next_route()

        t2 = perf_counter()
        time_sum += (t2-t1)
        # print('find_next_route {:.5f}'.format(t2-t1))


        t1 = perf_counter()

        print(f'cycle: {self.current_cycle}')
        print(f'current_position: {(agents[self.my_side].position.y, agents[self.my_side].position.x)}')
        print(f'target: {self.tron.target_pos} weight: {self.tron.get_wall_weight(self.tron.target_pos)}\n\n')

        self.tron.show_walls_info()

        t2 = perf_counter()
        time_sum += (t2-t1)
        # print('showing things {:.5f}'.format(t2-t1))
        

        if self.tron.is_wallbreaker_needed():
            if agents[self.my_side].wall_breaker_cooldown == 0:
                self.send_command(ActivateWallBreaker())

        next_dir = self.tron.next_dir()
        self.send_command(ChangeDirection(next_dir))

        print('overall_time: {:.5f}'.format(time_sum))
