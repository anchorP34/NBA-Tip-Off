# Bring in imports
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import numpy as np
from datetime import datetime
import argparse



def player_id(player_url):
    return player_url.replace('/players/','').replace('.html','')

def player_info(player_url):
    player_request = requests.get('https://www.basketball-reference.com{}'.format(player_url))
    player_soup = BeautifulSoup(player_request.text, 'lxml')

    player_name = player_soup.find_all('h1',attrs = {'itemprop':'name'})[0].text

    player_height = player_soup.find_all(attrs = {'itemprop':'height'})[0].text
    player_height_inches = int(player_height.split('-')[0]) * 12 + int(player_height.split('-')[1])
    player_birthday = player_soup.find_all(attrs = {'itemprop':'birthDate'})[0].text.replace('\n','').split()

    full_birthday_date = " ".join(player_birthday).replace(',','')
    birthday_datetime = datetime.strptime(full_birthday_date, '%B %d %Y')

    birth_year = birthday_datetime.year
    birth_month = birthday_datetime.month
    birth_day= birthday_datetime.day

    birth_yyyy_mm_dd = '{}-{}-{}'.format(birth_year, birth_month, birth_day)


    return {'Name': player_name
            , 'Height':player_height_inches
            , 'Birthday':birth_yyyy_mm_dd
           }

def check_player_existance(player_id):
    if player_id not in players:
        player_url = '/players/{}.html'.format(player_id)

        players[player_id] = player_info(player_url)
        print(players[player_id]['Name'], 'Has been added to the players dictionary','\n')


season_games = []
players = {}

season_request = requests.get('https://www.basketball-reference.com/leagues/NBA_{}_games.html'.format(2020))
season_soup = BeautifulSoup(season_request.text, 'lxml')

season_tbody = season_soup.find_all('tbody')[0]

for game in season_tbody.find_all('tr'):
    game_data = {}
    game_info = game.contents
    game_data['game_date'] = game_info[0].string
    game_data['game_away_team'] = game_info[2].string
    game_data['game_home_team'] = game_info[4].string
    game_data['game_url'] = game_info[6].contents[0].attrs['href']
    #print(game_data)
    #season_games.append(game_data)


    game_request = requests.get('https://www.basketball-reference.com/{}'.format(game_data['game_url'].replace('boxscores/','boxscores/pbp/')))
    game_soup = BeautifulSoup(game_request.text, 'lxml')

    print('https://www.basketball-reference.com/{}.html'.format(game_data['game_url'].replace('boxscores/','boxscores/pbp/')), 'Has Loaded')

    play_by_play = game_soup.find_all('tr')

    # Tip off
    while play_by_play[2].contents[3].text == '\xa0':
        play_by_play.pop(2)


    tip_off_players = play_by_play[2].contents[3].find_all('a')[:2]

    away_center_url = tip_off_players[0].attrs['href']
    away_center_player = player_id(away_center_url)

    home_center_url = tip_off_players[1].attrs['href']
    home_center_player = player_id(home_center_url)

    for player in [home_center_player, away_center_player]:
        check_player_existance(player)

    game_data['visiting_center'] = away_center_player
    game_data['home_center'] = home_center_player




    play_by_play_data = []

    # Play by play data until someone scores
    for idx, val in enumerate(play_by_play[3:]):
        play = val.contents
        visiting_team_event = play[3].text.replace('\xa0','')
        if visiting_team_event != '':
            posession = game_data['game_away_team']
            if play[3].a != None:
                visiting_player_url = play[3].a.attrs['href']
                visiting_team_player = player_id(visiting_player_url)
            else:
                visiting_team_player = ''
        else:
            visiting_team_player = ''

        home_team_event = play[7].text.replace('\xa0','')
        if home_team_event != '':
            posession = game_data['game_home_team']
            if play[7].a != None:
                home_player_url = play[7].a.attrs['href']
                home_team_player = player_id(home_player_url)
            else:
                home_team_player = ''
        else:
            home_team_player = ''

        score = play[5].text

        pbp = [visiting_team_event, visiting_team_player, home_team_event, home_team_player, score, posession]
        play_by_play_data.append(pbp)
        
        if score != '0-0':
            break

        for player in [home_team_player, visiting_team_player]:
            if player not in players and player != '':
                check_player_existance(player)

        if idx == 0:
            if home_team_event != '':
                game_data['winning_tip'] = 'home_center'
            else:
                game_data['winning_tip'] = 'away_center'

    game_data['Play By Play'] = pd.DataFrame(play_by_play_data, columns = ['Visiting Team Event','Visiting Team Player','Home Team Event','Home Team Player','Score','Possession'])
    season_games.append(game_data)
    print(game_data)