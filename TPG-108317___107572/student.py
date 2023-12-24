"""Example client."""
import asyncio
import getpass
import json
import os
import random
from collections import deque

import websockets

enemy_positions = []   
rock_positions = []
prev_move = " "                         #variable that stores the previous move (w,a,s,d)
double_jump = False                     #boolean variable that is activated whenever digdug is 1 block above the enemy
double_jump_key = ""                    #variable that stores the direction to move when double jumping/double movement
hold = False                            #boolean variable that is activated when there are no enemies in a distance <= 2 except a fygar 2 blocks under and digdug is correctly oriented to it
hold_next_key = " "                     #variable that stores the next direction that digdug will move after beeing on hold waiting for an oppurtunity to attack the fygar
rock_next = False                       #boolean variable that is activated whenever there is a rock in the next move expected ("s") for digdug.
rock_next_key = " "                     #variable that stores the move after checking that there is a rock under digdug and his movement is to move "s"
enemies_within_2 = 0                    #counter of enemies within a distance equal or less than 2
flygar_within_3 = 0                     #counter of fygars within a distance equal or less than 3
no_one = False                          #boolean variable that is activated if enemies_within_2 == 0 or (enemies_within_2 == 1 and enemy == fygar and  fygar_x != digdug_x) this will make DigDug move carefully to the fygar in the next move
closest_enemy_positions = []            #list that stores the last 100 positions of the closest enemy  (fygar stuck between 1 rock and a not escavated block)
closest_enemy_positions_loop = []       #list that stores the last 200 positions of the closest enemy (fygar is moving in loop between 2 positions)

MAX_POSITIONS = 100                     #number of positions to store in closest_enemy_positions
MAX_POSITIONS_LOOP = 200                #number of positions to store in closest_enemy_positions_loop

MOVEMENT = {
    "w": (0, -1),  # Move up
    "s": (0, 1),   # Move down
    "a": (-1, 0),  # Move left
    "d": (1, 0),   # Move right
}


async def agent_loop(server_address="localhost:8000", agent_name="student"):        
    """Example client loop."""
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        key= " "
        while True:
            try:
                state = json.loads(await websocket.recv())
                if "map" in state:
                    map_data = state["map"]
                if "digdug" in state:
                        update_enemy_positions(state)
                        update_rock_positions(state)
                        key = next_move(state,map_data)
                        await websocket.send(
                            json.dumps({"cmd": "key", "key": key})
                        )
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

def next_move(state,map_data):  #main function (every verification is done here), it returns the next movement to perform
    global prev_move
    global double_jump
    global double_jump_key
    global hold
    global no_one
    global rock_next_key
    global rock_next 
    global closest_enemy_positions          
    global closest_enemy_positions_loop
    global MAX_POSITIONS
    global MAX_POSITIONS_LOOP          #global initialization of variables

    key= " "                                    #action to be performed
    player_x, player_y = state["digdug"]        #digdug position
    enemies = state["enemies"]                  #enemies list

    if enemies is not None:    #if there are enemies

        closest_enemy = find_closest_enemy(player_x, player_y)                  #find the closest enemy
        closest_rock = find_closest_rock(player_x, player_y)                    #find the closest rock
        sorted_enemies = get_sorted_enemies_by_distance(player_x, player_y)     #sort enemies by distance to digdug
        
        if "map" in state:              #get map data
            map_data = state["map"]        

        if closest_enemy:       #if there is an enemy
            closest_enemy_positions.append((closest_enemy[0], closest_enemy[1]))            #add the position of the closest enemy to the list (list to prevent loop)
            closest_enemy_positions_loop.append((closest_enemy[0], closest_enemy[1]))       #add the position of the closest enemy to the list (list to prevent loop)

            distance_enemie = abs(player_x - closest_enemy[0]) + abs(player_y - closest_enemy[1])   #distance to the closest enemy
            distance_rock = abs(player_x - closest_rock[0]) + abs(player_y - closest_rock[1])       #distance to the closest rock
            
            if len(closest_enemy_positions) >= MAX_POSITIONS:                               #exists at least last 100 positions of the closest enemy  (fygar is stuck between 1 rock and a not escavated block and because we maintain a distance of 2 blocks between digdug and the enemy DigDUg would be wainting forever)
                #to prevent the infinite waiting we check if the last 100 positions of the closest enemy are the same and we move towards the enemy (knowing that we could die or kill him)
                closest_enemy_positions = closest_enemy_positions[-MAX_POSITIONS:]          #keep only the last 100 positions
                if all(pos == closest_enemy_positions[0] for pos in closest_enemy_positions[-MAX_POSITIONS:]):              #last 100 positions are the same
                    if distance_enemie == 2:                                                
                        if is_correctly_oriented(prev_move, closest_enemy[0], closest_enemy[1], player_x, player_y):        #if digdug is correctly oriented towards the closest enemy
                            if player_y - closest_enemy[1] < 0:                             #if digdug is above the enemy
                                key = "s"                                                   #move down to kill the enemy or die trying
                                prev_move = key                                             #update previous move with the new movement (so digdug can keep track of his orientation)
                                update_map_data(map_data, player_x, player_y, key)          #update map
                                return key                                                  #return action to be performed
                            elif player_y - closest_enemy[1] > 0:                           #if digdug is under the enemy (rest of the code uses the same logic as the previous if)
                                key = "w"                                                   
                                prev_move = key                                             #move up to kill the enemy or die trying
                                update_map_data(map_data, player_x, player_y, key)
                                return key
                            elif player_x - closest_enemy[0] < 0:
                                key = "d"                                                   #move right to kill the enemy or die trying
                                prev_move = key
                                update_map_data(map_data, player_x, player_y, key)
                                return key
                            else:
                                key = "a"                                                   #move left to kill the enemy or die trying
                                prev_move = key
                                update_map_data(map_data, player_x, player_y, key)
                                return key

            if len(closest_enemy_positions_loop) >= MAX_POSITIONS_LOOP:                     #exists at least last 200 positions of the closest enemy  (fygar is moving in a loop between 2 positions and because we maintain a distance of 2 blocks between digdug and the enemy DigDUg would be wainting forever)
                #to prevent the infinite waiting we check if the last 200 positions of the closest enemy are only 2 different blocks so we move away from the enemy (stoping the continuos loop, because fygar is not aware anymore that we are close to him, and give DigDug the opportunity to reorientate himself to the enemy)
                closest_enemy_positions_loop = closest_enemy_positions_loop[-MAX_POSITIONS_LOOP:]       #keep only the last 200 positions
                unique_positions = set(closest_enemy_positions_loop)                                    #keep only the unique positions (expected if in loop: only 2 positions)

                if distance_enemie == 2 and len(unique_positions) == 2:                     #if there are only 2 unique positions in the last 200 positions of the closest enemy and the distance to the enemy is 2 (DigDug maintains a security distance of 2 blocks between him and the enemy)
                    if player_y - closest_enemy[1] > 0:                    #if digdug is under the enemy
                        if is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, closest_enemy[0], closest_enemy[1], map_data, enemies):     #if moving down wont kill digdug and is a valid move  (trying to get away from the enemy)  
                            key = "s"               #move down to get away from the fygar and stop the loop              
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies):
                            key = "a"
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies):
                            key = "d"
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif is_valid_move(player_x, player_y - 1, map_data) and not will_die(player_x, player_y - 1, closest_enemy[0], closest_enemy[1], map_data, enemies):
                            key = "w"
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        else:
                            key = " "
                            update_map_data(map_data, player_x, player_y, key)
                            return key

                    elif player_y - closest_enemy[1] < 0:                   #if digdug is above the enemy
                        if is_valid_move(player_x, player_y - 1, map_data) and not will_die(player_x, player_y - 1, closest_enemy[0], closest_enemy[1], map_data, enemies):     #if moving up wont kill digdug and is a valid move  (trying to get away from the enemy)
                            key = "w"               #move up to get away from the fygar and stop the loop
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies):
                            key = "a"
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies):
                            key = "d"
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, closest_enemy[0], closest_enemy[1], map_data, enemies):
                            key = "s"
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        else:
                            key = " "
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                    else:
                        key = "A" 
                        update_map_data(map_data, player_x, player_y, key)
                        return key



            if rock_next == True:           #if there is a rock in the next move expected for digdug
                rock_next = False           #reset variable
                if prev_move == "d":        #if previous move was "d"   
                    if not will_die(player_x, player_y + 1, closest_enemy[0], closest_enemy[1], map_data, enemies) and is_valid_move(player_x, player_y + 1, map_data):  #if moving "s" wont kill digdug and is a valid move
                        key = "s"               #move down
                        hold = False            #reset hold variable so digdug can move normally next move
                        prev_move = key         #update previous move to keep track of the orientation of digdug
                        update_map_data(map_data, player_x, player_y, key)  #update map
                        return key            #return action to be performed
                    elif not will_die(player_x, player_y - 1, closest_enemy[0], closest_enemy[1], map_data, enemies) and is_valid_move(player_x, player_y - 1, map_data):
                        key = "w"
                        hold = False
                        prev_move = key
                        update_map_data(map_data, player_x, player_y, key)
                        return key
                    elif is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies):
                        key = "d"
                        hold = False
                        prev_move = key
                        update_map_data(map_data, player_x, player_y, key)
                        return key
                    elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies):
                        key = "a"
                        hold = False
                        prev_move = key
                        update_map_data(map_data, player_x, player_y, key)
                        return key
                    else:
                        key = " "
                        hold = False
                        update_map_data(map_data, player_x, player_y, key)
                        return key
                elif prev_move == "a":      #if previous move was "a" (rest of the code uses the same logic as the previous if)
                    if not will_die(player_x, player_y + 1, closest_enemy[0], closest_enemy[1], map_data, enemies) and is_valid_move(player_x, player_y + 1, map_data):
                        key = "s"
                        hold = False
                        prev_move = key
                        update_map_data(map_data, player_x, player_y, key)
                        return key
                    elif not will_die(player_x, player_y - 1, closest_enemy[0], closest_enemy[1], map_data, enemies) and is_valid_move(player_x, player_y - 1, map_data):
                        key = "w"
                        hold = False
                        prev_move = key
                        update_map_data(map_data, player_x, player_y, key)
                        return key
                    elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies):
                        key = "a"
                        hold = False
                        prev_move = key
                        update_map_data(map_data, player_x, player_y, key)
                        return key
                    elif is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies):
                        key = "d"
                        hold = False
                        prev_move = key
                        update_map_data(map_data, player_x, player_y, key)
                        return key
                    else:
                        key = " "
                        hold = False
                        update_map_data(map_data, player_x, player_y, key)
                        return key
                else:
                    print("rip")
                    
                

            if hold == True or no_one == False:    #if Dig Dug is on hold (waiting for the right moment) or there are no enemies in a distance <= 2 except a fygar 2 blocks under and digdug is correctly oriented to it

                if no_one == False:     # digdug will try to move carefully to the fygar
                    key = move_carefully__to_fygar(player_x, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies,sorted_enemies)    #call function to understand the best movement to perform when DigDUg needs to get to the fygar in a safe way
                    if key == " ":  #if the best movement is to stand still
                        update_map_data(map_data, player_x, player_y, key)  #update map
                        return key
                    else:   #if the best movement is to move
                        prev_move = key    #update previous move with the new movement (so digdug can keep track of his orientation)
                        update_map_data(map_data, player_x, player_y, key)  #update map
                        return key
                    
                else:   #if Dig Dug is on hold (waiting for the right moment)
                    no_one = False  #reset variable (digdug will try to move carefully to the fygar in next move)
                    if hold_next_key == "w":    #if the movement after standing still waiting for the right moment is to move up
                        if is_valid_move(player_x, player_y - 1, map_data) and not will_die(player_x, player_y - 1, closest_enemy[0], closest_enemy[1], map_data, enemies):  #if moving up wont kill digdug and is a valid move
                            key = "w"               #move up
                            hold = False            #reset hold variable so digdug can move normally next move
                            prev_move = key         #update previous move to keep track of the orientation of digdug
                            update_map_data(map_data, player_x, player_y, key)  #update map
                            return key              #return action to be performed
                        elif not will_die(player_x - 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies) and is_valid_move(player_x - 1, player_y, map_data):
                            key = "a"
                            hold = False
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif not will_die(player_x + 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies) and is_valid_move(player_x + 1, player_y, map_data):
                            key = "d"
                            hold = False
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif not will_die(player_x, player_y + 1, closest_enemy[0], closest_enemy[1], map_data, enemies) and is_valid_move(player_x, player_y + 1, map_data):
                            key = "s"
                            hold = False
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        else:
                            key = " "
                            hold = False
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                            
                    elif hold_next_key == "s":  #same logic as the previous if
                        if is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, closest_enemy[0], closest_enemy[1], map_data, enemies):
                            key = "s"
                            hold = False
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif not will_die(player_x - 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies) and is_valid_move(player_x - 1, player_y, map_data):
                            key = "a"
                            hold = False
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif not will_die(player_x + 1, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies) and is_valid_move(player_x + 1, player_y, map_data):
                            key = "d"
                            hold = False
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        elif not will_die(player_x, player_y - 1, closest_enemy[0], closest_enemy[1], map_data, enemies) and is_valid_move(player_x, player_y - 1, map_data):
                            key = "w"
                            hold = False
                            prev_move = key
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        else:
                            key = " "
                            hold = False
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                    else:       #hold is only performed if enemy is above or under digdug in the same x position
                        print("rip")
                    
            if distance_rock == 1:       #if there is a rock in a distance == 1                         
                key =  circle_rock(player_x, player_y, closest_rock[0], closest_rock[1], closest_enemy[0], closest_enemy[1],map_data,enemies)   #call function to decide the next movement to avoid the rock (circle it)
                if key == " ":                                              #if the best movement is to stand still
                    update_map_data(map_data, player_x, player_y, key)      #update map
                    return key                                              #return action to be performed
                else:                    #if the best movement is to move
                    prev_move = key                                         #update previous move with the new movement (so digdug can keep track of his orientation)
                    update_map_data(map_data, player_x, player_y, key)      #update map
                    return key                                              #return action to be performed
            if double_jump == True:   #digdug should perform a double movement (normmally used to avoid enemies are next to each other and want to maintain a distance of 2 blocks and by this could reorientate digdug to the closest enemy)
                double_jump = False   #reset variable
                dbj = double_jump_key   
                key = double_jump_valid(dbj,player_x, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies)  #verify if the double movement is valid and if not perform another movement
                if key == " ":          #if the best movement is to stand still   
                    update_map_data(map_data, player_x, player_y, key)  #update map
                    return key          #return action to be performed
                else:                   #if the best movement is to move
                    prev_move = key     #update previous move with the new movement (so digdug can keep track of his orientation)
                    update_map_data(map_data, player_x, player_y, key)  #update map
                    return key          #return action to be performed
                
            if Pooka_wallpassing(player_x, player_y, enemies):              #if there is a Pooka in a distance <= 2 and it is wallpassing                             
                if is_correctly_oriented(prev_move, closest_enemy[0], closest_enemy[1], player_x, player_y):        #if digdug is correctly oriented towards Pooka
                    blocks = blocks_between(player_x, player_y, closest_enemy[0], closest_enemy[1], map_data)       #calculate the blocks between digdug and Pooka
                    blocks_escavated = all_blocks_excavated(map_data, blocks)                                       #verify if all blocks between digdug and Pooka are escavated
                    if blocks_escavated:                                                                            #if all blocks are escavated
                        key = "A"                                                                                   #attack the Pooka
                        return key                                                                                  #return action to be performed
                
                key = avoid_Pooka(player_x, player_y, enemies,map_data)     #function to decide the next movement to avoid the Pooka (defensive movement)
                if key == " ":              #if the best movement is to stand still
                    update_map_data(map_data, player_x, player_y, key)      #update map
                    return key                                              #return action to be performed
                else:                       #if the best movement is to move                                 
                    prev_move = key         
                    update_map_data(map_data, player_x, player_y, key)
                    return key
            elif Flygar_fire(player_x, player_y, enemies):                  #if there is a fygar in a distance <= 2 and it is firing                                      
                key =  avoid_fire(player_x, player_y, enemies,map_data)     #function to decide the next movement to avoid the fire (defensive movement)  
                if key == " ":              #if the best movement is to stand still
                    update_map_data(map_data, player_x, player_y, key)      #update map
                    return key                                              #return action to be performed
                else:                       
                    prev_move = key
                    update_map_data(map_data, player_x, player_y, key)
                    return key
            elif can_pump_enemy(distance_enemie, closest_enemy[2]):                                                 #verification if it is possible to shoot enemies (verification of game rules)
                value = is_correctly_oriented(prev_move, closest_enemy[0], closest_enemy[1], player_x, player_y)    #verification if digdug is correctly oriented towards the closest enemy
                if value == True:                           #correctly oriented
                    if player_x == closest_enemy[0]:        #if digdug and enemy are in the same x position   
                        if closest_enemy[2] == "Fygar":                                                         #closest enemy is a fygar
                            if player_y - closest_enemy[1] > 1 or player_y - closest_enemy[1] < -1:             #if digdug is more than 2 blocks of distance to the fygar in the y position
                                blocks = blocks_between(player_x, player_y, closest_enemy[0], closest_enemy[1], map_data)     #calculate the blocks between digdug and fygar
                                blocks_escavated = all_blocks_excavated(map_data, blocks)                                               #verify if all blocks between digdug and fygar are escavated
                                if blocks_escavated:        #all blocks escavated 
                                    return "A"              #shoot the fygar
                                else:                       #not all blocks escavated
                                    key = move_carefully__to_fygar(player_x, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies,sorted_enemies)        #call function to decide the next movement to perform when there is a fygar (sometimes dugdug holds position waiting for the right moment to attack)
                                    if key == " ":          #if the best movement is to stand still
                                        update_map_data(map_data, player_x, player_y, key)      
                                        return key
                                    else:                   #if the best movement is to move
                                        prev_move = key     #update previous move with the new movement (so digdug can keep track of his orientation)
                                        update_map_data(map_data, player_x, player_y, key)
                                        return key
                            else:                           #if digdug is 2 blocks of distance to the fygar in the y position
                                return "A"
                        else:                               #closest enemy is a pooka
                            return "A"
                    else:                                   #if digdug and enemy are not in the same x position
                        return "A"
                    
                else:                                       #not correctly oriented
                    if distance_enemie == 2:                
                        key = convert_direction_to_key_avoid_Pooka(player_x, player_y, closest_enemy[0], closest_enemy[1], map_data, enemies)       #call function to decide the next movement to perform when there is ana enemy nearby (defensive movement)
                        if key == " ":              #if the best movement is to stand still
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                        else:                       #if the best movement is to move
                            double_jump = True      #activate double jump variable (it will be used in the next move and will permit digdug to perform a double movement and by this rotating himself correctly and safely to the closest enemy)
                            double_jump_key = key   #store the direction of the next movement to perform
                            prev_move = key         #update previous move with the new movement (so digdug can keep track of his orientation)
                            update_map_data(map_data, player_x, player_y, key)
                            return key
                    else:
                        key = orient_towards_enemy(prev_move, closest_enemy[0], closest_enemy[1], map_data, player_x, player_y, enemies)        #call function to orient digdug towards the closest enemy because he is not correctly oriented and its safe to do so
                        prev_move = key
                        update_map_data(map_data, player_x, player_y, key)
                        return key
            else:  
                key = convert_direction_to_key(player_x, player_y, closest_enemy[0], closest_enemy[1], map_data)        #movement to get closer to the closest enemy              
                prev_move = key
                update_map_data(map_data, player_x, player_y, key)
                return key
            
    update_map_data(map_data, player_x, player_y, key)
    return key


def update_map_data(map_data, player_x, player_y, key):     #function to update the map, if the block is escavated block = 0 (always depending on digdugs position and movement)
    if key == "w":
        map_data[player_x][player_y - 1] = 0
    elif key == "s":
        map_data[player_x][player_y + 1] = 0
    elif key == "a":
        map_data[player_x - 1][player_y] = 0
    elif key == "d":
        map_data[player_x + 1][player_y] = 0
    else:
        print("acho que isto basta")
        
        

def all_blocks_excavated(map_data, blocks):     #function to verify if all blocks given as an argument are escavated (their value is 0)
    # Check if all blocks in the list are excavated
    for block in blocks:
        x, y = block
        if map_data[x][y] == 1:
            return False
    return True

def blocks_between(player_x, player_y, enemy_x, enemy_y, map_data): 
    # Calculate the blocks between player and enemy
    blocks = []

    # Check x direction
    dx = enemy_x - player_x
    if dx != 0:
        step_x = dx // abs(dx)
        for x in range(player_x + step_x, enemy_x, step_x):
            blocks.append((x, player_y))            #add the blocks between digdug and the enemy to a list

    # Check y direction
    dy = enemy_y - player_y
    if dy != 0:
        step_y = dy // abs(dy)
        for y in range(player_y + step_y, enemy_y, step_y):
            blocks.append((enemy_x, y))             #add the blocks between digdug and the enemy to a list

    return blocks

def move_carefully__to_fygar(player_x, player_y, enemy_x, enemy_y, map_data, enemies, sorted_enemies):
    # Function to devcide the next movement when there is a fygar in a distance <= 2 or 3
    global hold_next_key
    global hold
    global enemies_within_2
    global no_one
    global blocks
    global prev_move        #global initialization of variables

    global flygar_within_3
    for enemy in enemies:  
        if abs(enemy["pos"][0] - player_x) + abs(enemy["pos"][1] - player_y) <= 2:
            enemies_within_2 += 1       #enemies within a distance <= 2 counter
        if enemy["name"] == "Fygar":        
            if enemy["pos"][0] == player_x:
                if abs(enemy["pos"][1] - player_y) <= 3:
                    flygar_within_3 += 1    #fygar within a distance <= 3 counter
        
    if enemies_within_2 > 1:    
        # There is more than one enemy closer than distance <= 2
        enemies_within_2 = 0    #reset counter
        flygar_within_3 = 0     #reset counter
        return convert_direction_to_key_avoid_Pooka(player_x, player_y, enemy_x, enemy_y, map_data, enemies)    #call function to execute a movement that avoids enemies  (defensive movement)
    elif enemies_within_2 == 1:  
        # There is only one enemy closer than distance <= 2
        enemies_within_2 = 0 
        flygar_within_3 = 0  
        if sorted_enemies[0][2] == "Fygar":     #if the closest enemy is a fygar
            if player_x == enemy_x:             #if digdug and fygar are in the same x position
                blocks = blocks_between(player_x, player_y, enemy_x, enemy_y, map_data)  #calculate the blocks between digdug and fygar
                blocks_escavated_2 = all_blocks_excavated(map_data, blocks)     #verify if all blocks between digdug and fygar are escavated
                if blocks_escavated_2:        #if all blocks are escavated
                    return "A"                #attack the fygar
                if player_y - enemy_y > 0:      #if digdug is under the fygar
                    key = " "                   #next movement is to stand still
                    hold_next_key = "w"         #next movement after standing still is to move up  (trying to get under the fygar but waiting for the right moment)
                    hold = True                 #activation of the hold variable to permit DigDug to stand still next move
                    update_map_data(map_data, player_x, player_y, key)  #update the map
                    return key
                elif player_y - enemy_y < 0:    #if digdug is above the fygar (rest of the code uses the same logic as the previous if)
                    key = " "               
                    hold_next_key = "s"
                    hold = True
                    update_map_data(map_data, player_x, player_y, key)
                    return key
            else:                            #if digdug and fygar are not in the same x position (next ac)
                enemies_within_2 = 0
                flygar_within_3 = 0
                no_one = True       #permits digdug to not move carefully to the fygar int the next move (if it is False digdug will try to move carefully to the fygar)
                return " "
        else:
            #It is a Pooka so shoot it
            enemies_within_2 = 0
            flygar_within_3 = 0
            return "A"
    else:   #no enemies within a distance <= 2
        if flygar_within_3 > 0:   #if there is a fygar within a distance <= 3
            flygar_within_3 = 0
            enemies_within_2 = 0

            blocks_fygar = blocks_between(player_x, player_y, enemy_x, enemy_y, map_data)     #calculate the blocks between digdug and fygar
            blocks_escavated_fygar = all_blocks_excavated(map_data, blocks_fygar)                       #verify if all blocks between digdug and fygar are escavated
            if blocks_escavated_fygar:      #if all blocks are escavated
                return "A"                  #attack the fygar
            else:               #if not all blocks are escavated
                if player_y - enemy_y > 0:    #if digdug is under the fygar
                    key = " "               #next movement is to stand still
                    hold_next_key = "w"     #next movement after standing still is to move up  (trying to get under the fygar but waiting for the right moment)
                    hold = True             #activation of the hold variable to permit DigDug to stand still next move
                    update_map_data(map_data, player_x, player_y, key)    #update the map
                    return key
                elif player_y - enemy_y < 0:    #if digdug is above the fygar (rest of the code uses the same logic as the previous if)
                    key = " "
                    hold_next_key = "s"
                    hold = True
                    update_map_data(map_data, player_x, player_y, key)
                    return key
        else:  #no fygar within a distance <= 3
            enemies_within_2 = 0
            flygar_within_3 = 0
            no_one = True        #permits digdug to not move carefully to the fygar int the next move (if it is False digdug will try to move carefully to the fygar)
            return " "
       

def double_jump_valid(dbj,player_x, player_y, enemy_x, enemy_y, map_data, enemies):         #function to decide the movement of digdug after deciding to perform a double movement
    #verification if digdug position is in one of the 4 of corners the map
    if  (abs(enemy_x - player_x) + abs(enemy_y - player_y) == 2) and player_x == 0 and player_y == 0:
        return " "
    elif (abs(enemy_x - player_x) + abs(enemy_y - player_y) == 2) and player_x == 0 and player_y == 23:
        return " "
    elif (abs(enemy_x - player_x) + abs(enemy_y - player_y) == 2) and player_x == 47 and player_y == 0:
        return " "
    elif (abs(enemy_x - player_x) + abs(enemy_y - player_y) == 2) and player_x == 47 and player_y == 23:
        return " "
    else:   #not in a corner position
        if dbj == "a":  #next movement based on the previous one is "a"
            if is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):   #verification if the position where digdug is moving is valid and if he wont die moving there
                return "a"
            elif is_valid_move(player_x, player_y - 1, map_data) and not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies):
                return "w"
            elif is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, enemy_x, enemy_y, map_data, enemies):
                return "s"
            else:
                return " "
        elif dbj == "d":
            if is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):
                return "d"
            elif is_valid_move(player_x, player_y - 1, map_data) and not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies):
                return "w"
            elif is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, enemy_x, enemy_y, map_data, enemies):
                return "s"
            else:
                return " "
        elif dbj == "w":
            if is_valid_move(player_x, player_y - 1, map_data) and not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies):
                return "w"
            elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):
                return "a"
            elif is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):
                return "d"
            else:
                return " "
        elif dbj == "s":
            if is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, enemy_x, enemy_y, map_data, enemies):
                return "s"
            elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):
                return "a"
            elif is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):
                return "d"
            else:
                return " "
        else:       #hold position
            return " "      

def is_correctly_oriented(prev_move, enemy_x, enemy_y, player_x, player_y):     
    # Check if Dig Dug is correctly oriented towards the enemy based on the previous move
    if prev_move == "d" and player_x - enemy_x < 0 and player_y - enemy_y == 0:     #based on the previous move verifies if their orientation is the correct (is oriented towards the closest enemy)
        return True
    elif prev_move == "a" and player_x - enemy_x > 0 and player_y - enemy_y == 0:
        return True
    elif prev_move == "s" and player_y - enemy_y < 0 and player_x - enemy_x == 0:
        return True
    elif prev_move == "w" and player_y - enemy_y > 0 and player_x - enemy_x == 0:
        return True
    else:
        return False

def orient_towards_enemy(prev_move, enemy_x, enemy_y, map_data, player_x, player_y, enemies):   
    # Orient Dig Dug towards the enemy based on the previous move
    dx = enemy_x - player_x
    dy = enemy_y - player_y

    # Calculate distances to enemies in each direction
    distances = {
        "w": calculate_distance_to_enemies(player_x, player_y - 1),
        "s": calculate_distance_to_enemies(player_x, player_y + 1),
        "a": calculate_distance_to_enemies(player_x - 1, player_y),
        "d": calculate_distance_to_enemies(player_x + 1, player_y),
    }

    # Sort directions by distance to enemies in descending order
    sorted_directions = sorted(distances.keys(), key=lambda key: distances[key], reverse=True)

    # Check if moving right is a valid move
    if dx > 0 and is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):
        return "d" 

    # Check if moving left is a valid move
    elif dx < 0 and is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):
        return "a"

    # Check if moving down is a valid move
    elif dy > 0 and is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, enemy_x, enemy_y, map_data, enemies):
        return "s"

    # Check if moving up is a valid move
    elif dy < 0 and is_valid_move(player_x, player_y - 1, map_data) and  not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies):
        return "w"

    # Attempt to find an alternative direction that maximizes the distance from enemies
    for direction in sorted_directions:
        if is_valid_move(player_x + MOVEMENT[direction][0], player_y + MOVEMENT[direction][1], map_data) and not will_die(player_x + MOVEMENT[direction][0], player_y + MOVEMENT[direction][1], enemy_x, enemy_y, map_data, enemies):
            return direction

    # If all moves are blocked or result in death, stay in the same position
    return " "

def calculate_distance_to_enemies(x, y):
    # Calculate the total distance from the specified position to all enemies
    return sum(abs(x - enemy_x) + abs(y - enemy_y) for enemy_x, enemy_y, _ in enemy_positions)


def will_die(new_x, new_y, enemy_x, enemy_y, map_data, enemies):
    # Check if Dig Dug will die by moving to the specified position
    if new_x == enemy_x and new_y == enemy_y:
        return True

    # Check if there is fire in the specified position
    for enemy in enemies:
        if enemy["name"] == "Fygar" and "fire" in enemy:
            fire_positions = enemy["fire"]
            if [new_x, new_y] in fire_positions:
                return True

    return False


def convert_direction_to_key(player_x, player_y, enemy_x, enemy_y, map_data):     
    #Based on Enemy and Dig Dug position decide the next movement

    dx = enemy_x - player_x     #verify if enemy is left or right to the Dig Dug
    dy = enemy_y - player_y     #verify if enemy is above or under Dig Dug

    if dx > 0:      #enemy at the right of the Dig Dug
        if is_valid_move(player_x + 1, player_y, map_data):     #move is for outside the map boundaries
            return "d"  # Move right
        elif is_valid_move(player_x, player_y - 1, map_data):   
            return "w"
        else:
            return "s"
    elif dx < 0:    #enemy at the left of the Dig Dug
        if is_valid_move(player_x - 1, player_y, map_data):
            return "a"  # Move left
        elif is_valid_move(player_x, player_y - 1, map_data):
            return "w"
        else:
            return "s"
    elif dy > 0:    #enemy under Dig Dug
        if is_valid_move(player_x, player_y + 1, map_data):
            return "s"  # Move down
        elif is_valid_move(player_x - 1, player_y, map_data):
            return "a"
        else:
            return "d"  
    elif dy < 0:    #enemy above Dig Dug
        if is_valid_move(player_x, player_y - 1, map_data):
            return "w"  # Move up
        elif is_valid_move(player_x - 1, player_y, map_data):
            return "a"
        else:
            return "d"
    
    return " "

def is_valid_move(x, y, map_data):      
    # Check if the move is within the map boundaries
    map_width = len(map_data[0])
    map_height = len(map_data)
    return 0 <= y < map_width and 0 <= x < map_height


def update_rock_positions(state):   
    # Updates rock positions on the map
    global rock_positions
    rocks = state["rocks"]
    rock_positions = [(rock["pos"][0], rock["pos"][1]) for rock in rocks]

def update_enemy_positions(state):
    # Updates enemy positions on the map
    global enemy_positions
    enemies = state["enemies"]
    enemy_positions = [(enemy["pos"][0], enemy["pos"][1], enemy["name"]) for enemy in enemies]


def can_pump_enemy(distance_enemy, enemy_name):
    # Check if Dig Dug can pump the enemy
    if distance_enemy <= 3 and enemy_name == "Fygar":
        return True
    elif distance_enemy <= 3 and enemy_name == "Pooka":
        return True
    else:
        return False
    

def find_closest_rock(player_x, player_y):
    # Find the closest rock to Dig Dug
    if rock_positions:
        return min(rock_positions, key=lambda r: abs(r[0] - player_x) + abs(r[1] - player_y))

def circle_rock(player_x, player_y, rock_x, rock_y, enemy_x, enemy_y,map_data,enemies):
    # Attempt to circle the rock
    global rock_next_key
    global rock_next
    global prev_move                                        #global initialization of variables
    dx, dy = rock_x - player_x, rock_y - player_y           #calculate the distance between digdug and the rock (to know if the rock is at the right or left of digdug)

    if dx > 0 and dy == 0:                                  #rock at the right of digdug (having the same y position))   
        #first option of movement is to move up, second option is to move left, third option is to move down      
        if not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies) and is_valid_move(player_x, player_y - 1, map_data):       #verification if the position where digdug is moving is valid and if he wont die moving there
            key = "w"                                                                                                                           #if yes, key = "w"
            update_map_data(map_data, player_x, player_y, key)                                                                                                              #next movement after moving up is to move right (trying to get under the rock but waiting for the right moment)
            prev_move = key
            return key                                     #move up
        elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies): 
            key = "a"  
            update_map_data(map_data, player_x, player_y, key)                                                                                                              #next movement after moving up is to move right (trying to get under the rock but waiting for the right moment)
            prev_move = key
            return key                                      
        elif not will_die(player_x, player_y + 1, enemy_x, enemy_y, map_data, enemies) and is_valid_move(player_x, player_y + 1, map_data):
            key = "s"
            update_map_data(map_data, player_x, player_y, key)                                                                                                              #next movement after moving up is to move right (trying to get under the rock but waiting for the right moment)
            prev_move = key
            return key  
        else:
            return " "
    if dx == 0 and dy > 0:                                  #rock under digdug (having the same x position)
        if enemy_x - player_x == 0 and (enemy_y - player_y) > 0:        #if digdug and enemy are in the same x position and the enemy is under digdug (this was a present loop so DigDug have to take fixed movements to avoid it)
            if is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):   #verification if the position where digdug is moving is valid and if he wont die moving there
                key = "d"                   #move right
                rock_next_key = "s"         #next movement after moving right is to move down (trying to get to get to the rifht of the rock, circling it)
                rock_next = True            #activation of the rock_next variable to permit DigDug to perform a double movement, with a fixed next movement
                update_map_data(map_data, player_x, player_y, key)      
                prev_move = key
                return key
            elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):
                key = "a"
                rock_next_key = "s"
                rock_next = True
                update_map_data(map_data, player_x, player_y, key)
                prev_move = key
                return key
            else:               #if digdug cant move right or left (because of the rock or the enemy) he will move up, to avoid the enemy and staying in distance from the rock
                key = "w"
                update_map_data(map_data, player_x, player_y, key)
                prev_move = key
                return key

        #no enemy under digdug (no present loop) 
        if not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies) and is_valid_move(player_x, player_y - 1, map_data):       
            key = "w"
            update_map_data(map_data, player_x, player_y, key)                                                                                                              
            prev_move = key
            return key  
        elif is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):
            key = "d"
            update_map_data(map_data, player_x, player_y, key)                                                                                                             
            prev_move = key
            return key  
        elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):
            key = "a"
            update_map_data(map_data, player_x, player_y, key)                                                                                                              
            prev_move = key
            return key  
        else:
            return " "
    if dx < 0 and dy == 0:                            #rock at the left of digdug (having the same y position)
        if not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies) and is_valid_move(player_x, player_y - 1, map_data):
            key = "w"
            update_map_data(map_data, player_x, player_y, key)                                                                                                              
            prev_move = key
            return key  
        elif not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies) and is_valid_move(player_x + 1, player_y, map_data):
            key = "d"
            update_map_data(map_data, player_x, player_y, key)                                                                                                              
            prev_move = key
            return key  
        elif is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, enemy_x, enemy_y, map_data, enemies):
            key = "s"
            update_map_data(map_data, player_x, player_y, key)                                                                                                             
            prev_move = key
            return key  
        else:
            return " "
    if dx == 0 and dy < 0:                          #rock above digdug (having the same x position)
        if is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):
            key = "d"
            update_map_data(map_data, player_x, player_y, key)                                                                                                              #next movement after moving up is to move right (trying to get under the rock but waiting for the right moment)
            prev_move = key
            return key  
        elif not will_die(player_x, player_y + 1, enemy_x, enemy_y, map_data, enemies) and is_valid_move(player_x, player_y + 1, map_data):
            key = "s"
            update_map_data(map_data, player_x, player_y, key)                                                                                                              #next movement after moving up is to move right (trying to get under the rock but waiting for the right moment)
            prev_move = key
            return key  
        elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):
            key = "a"
            update_map_data(map_data, player_x, player_y, key)                                                                                                              #next movement after moving up is to move right (trying to get under the rock but waiting for the right moment)
            prev_move = key
            return key  
        else:
            return " "
    return " "  # No movement by default

def find_closest_enemy(player_x, player_y):
    # Find the closest enemy to Dig Dug
    if enemy_positions:
        return min(enemy_positions, key=lambda e: abs(e[0] - player_x) + abs(e[1] - player_y))
    

def convert_direction_to_key_avoid_Pooka(player_x, player_y, enemy_x, enemy_y, map_data,enemies):
    # Based on the position of the Pooka and Dig Dug decide the next movement (DigDug will try to avoid the Pooka by moving in the opposite direction)
    dx = enemy_x - player_x
    dy = enemy_y - player_y

    # Check if Dig Dug is in one of the 4 corners of the map
    if  abs(enemy_x - player_x) + abs(enemy_y - player_y) == 2 and player_x == 0 and player_y == 0:
        return " "
    elif abs(enemy_x - player_x) + abs(enemy_y - player_y) == 2 and player_x == 0 and player_y == 23:
        return " "
    elif abs(enemy_x - player_x) + abs(enemy_y - player_y) == 2 and player_x == 47 and player_y == 0:
        return " "
    elif abs(enemy_x - player_x) + abs(enemy_y - player_y) == 2 and player_x == 47 and player_y == 23:
        return " "
    else:   # Not in a corner position
        if dx > 0:        # Pooka is at the right of Dig Dug
            if is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):   # Check if moving left is a valid move and will not cause death
                key = "a"
                return key
            elif is_valid_move(player_x, player_y - 1, map_data) and not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies):
                key = "w"
                return key
            elif is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y  + 1, enemy_x, enemy_y, map_data, enemies):
                key = "s"
                return key
            else:
                return " "
                
        elif dx < 0:
            if is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):
                key = "d"
                return key
            elif is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, enemy_x, enemy_y, map_data, enemies):
                key = "s"
                return key
            elif is_valid_move(player_x, player_y - 1, map_data) and  not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies):
                key = "w"
                return key
            else:
                return " "

        elif dy > 0:
            if is_valid_move(player_x, player_y - 1, map_data) and not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies):
                key = "w"
                return key
            elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):
                key = "a"
                return key
            elif is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):
                key = "d"
                return key
            else:
                return " "
        elif dy < 0:
            if is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, enemy_x, enemy_y, map_data, enemies):
                key = "s"
                return key
            elif is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):
                key = "a"
                return key
            elif is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):
                key = "d"
                return key
            else:
                return " "

        return " "


def convert_direction_to_key_avoid_Fire(player_x, enemy_x,player_y, enemy_y, enemies, map_data): 
    # Based on the position of the Fygar and Dig Dug decide the next movement (DigDug will try to avoid the Fygar's fire by moving in the opposite direction)
    dx = enemy_x - player_x

    if dx > 0:      #testar trocar subir/descer antes das laterais
        if is_valid_move(player_x - 1, player_y, map_data) and not will_die(player_x - 1, player_y, enemy_x, enemy_y, map_data, enemies):
            key = "a"
            return key
        elif is_valid_move(player_x, player_y - 1, map_data) and not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies):
            key = "w"
            return key
        elif is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y  + 1, enemy_x, enemy_y, map_data, enemies):
            key = "s"
            return key
        else:
            return " "
    elif dx < 0:
        if is_valid_move(player_x + 1, player_y, map_data) and not will_die(player_x + 1, player_y, enemy_x, enemy_y, map_data, enemies):
            key = "d"
            return key
        elif is_valid_move(player_x, player_y + 1, map_data) and not will_die(player_x, player_y + 1, enemy_x, enemy_y, map_data, enemies):
            key = "s"
            return key
        elif is_valid_move(player_x, player_y - 1, map_data) and  not will_die(player_x, player_y - 1, enemy_x, enemy_y, map_data, enemies):
            key = "w"
            return key
        else:
            return " "
    else:
        return " "

def Pooka_wallpassing(player_x, player_y, enemies):
    # Check if Pooka is wallpassing (moving through walls)
    for enemy in enemies:
        if enemy["name"] == "Pooka" and "traverse" in enemy:
            distance = abs(player_x - enemy["pos"][0]) + abs(player_y - enemy["pos"][1])
            return distance <= 3        
    return False

def avoid_Pooka(player_x, player_y, enemies, map_data):
    # Verify if Dig Dug can avoid Pooka and calls the function to do so
    for enemy in enemies:
        if enemy["name"] == "Pooka":
            return convert_direction_to_key_avoid_Pooka(player_x, player_y, enemy["pos"][0], enemy["pos"][1], map_data,enemies)
    return " "

def Flygar_fire(player_x, player_y, enemies):
    #Check if Fygar's firing and is in range
    for enemy in enemies:
        if enemy["name"] == "Fygar" and "fire" in enemy:
            distance = abs(player_x - enemy["pos"][0]) + abs(player_y - enemy["pos"][1])
            return distance <= 4
    return False

def avoid_fire(player_x, player_y, enemies,map_data):
    # Verify if Dig Dug can avoid Fygar's fire and calls the function to do so
    for enemy in enemies:
        if enemy["name"] == "Fygar" and "fire" in enemy:
            return convert_direction_to_key_avoid_Fire(player_x, enemy["pos"][0], player_y, enemy["pos"][1], enemies, map_data)
    return " "

def get_sorted_enemies_by_distance(player_x, player_y):
    # Sort enemies by distance to Dig Dug
    if enemy_positions:
        sorted_enemies = sorted(enemy_positions, key=lambda e: abs(e[0] - player_x) + abs(e[1] - player_y))
        return [(x, y, name) for x, y, name in sorted_enemies]
    else:
        return []


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))