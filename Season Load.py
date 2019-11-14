# Bring in imports
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import numpy as np
from datetime import datetime
import argparse
import json


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
    birth_month = '0{}'.format(birthday_datetime.month) if birthday_datetime.month < 10 else birthday_datetime.month
    birth_day= birthday_datetime.day

    birth_yyyy_mm_dd = '{}-{}-{}'.format(birth_year,  birth_month, birth_day)


    return {'Name': player_name
            , 'Height':player_height_inches
            , 'Birthday':birth_yyyy_mm_dd
           }

def check_player_existance(player_id):
    if player_id not in players:
        player_url = '/players/{}.html'.format(player_id)

        players[player_id] = player_info(player_url)
        print(players[player_id]['Name'], 'Has been added to the players dictionary','\n')



# Seasons that need to be parsed
for season in [2019,2020]:
    print("\n\n\n\n{} season is loading...\n\n\n\n".format(season))
    bad_games = []
    season_games = []
    players = {}

    all_listed_games = []

    months = ['october','november','december','january','february','march','april','may','june']

    for m in months:
        season_request = requests.get('https://www.basketball-reference.com/leagues/NBA_{}_games-{}.html'.format(season,m))
        season_soup = BeautifulSoup(season_request.text, 'lxml')

        try:
            season_tbody = season_soup.find_all('tbody')[0]

            for game in season_tbody.find_all('tr'):
                if game.contents[6].text == 'Box Score':
                    all_listed_games.append(game)
        except IndexError:
            # There are no final games for this month
            pass

    print("Total Games: ",len(all_listed_games))
    for game in all_listed_games:
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

        print('https://www.basketball-reference.com/{}'.format(game_data['game_url'].replace('boxscores/','boxscores/pbp/')), 'Has Loaded')

        play_by_play = game_soup.find_all('tr')

        try:
            # Tip off
            while play_by_play[2].contents[3].text.startswith("Jump") == False:
                play_by_play.pop(2)


            tip_off_players = play_by_play[2].contents[3].find_all('a')[:2]
            #print(tip_off_players)

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

                for player in [home_team_player, visiting_team_player]:
                    if player not in players and player != '':
                        check_player_existance(player)

                if idx == 0:
                    if home_team_event != '':
                        game_data['winning_tip'] = 'home_center'
                    else:
                        game_data['winning_tip'] = 'away_center'

                if score != '0-0':
                    break

            game_data['Play By Play'] = pd.DataFrame(play_by_play_data, columns = ['Visiting Team Event','Visiting Team Player','Home Team Event','Home Team Player','Score','Possession'])
            season_games.append(game_data)
            print(game_data)
        except IndexError:
            # Some games don't show the tip off
            print('https://www.basketball-reference.com/{}'.format(game_data['game_url'].replace('boxscores/','boxscores/pbp/')), 'is a bad game')
            bad_games.append('https://www.basketball-reference.com/{}'.format(game_data['game_url'].replace('boxscores/','boxscores/pbp/')))
            pass

    bad_games_df = pd.DataFrame(bad_games, columns = ['Bad Games'])
    bad_games_df.to_csv("{} Bad Games.csv".format(season), index = False)

    season_df_columns = ['season','game_date', 'game_away_team', 'game_home_team', 'game_url',
       'visiting_center', 'home_center', 'winning_tip', 'Visiting Team Event',
       'Visiting Team Player', 'Home Team Event', 'Home Team Player', 'Score',
       'Possession']

    season_df = pd.DataFrame(columns = season_df_columns)

    for game in season_games:
        df = pd.DataFrame([season], columns = ['season'])
        for col in [col for col in game if col not in ['Play By Play']]:
            df[col] = game[col]
        final_df = df.assign(key=1).merge(game['Play By Play'].assign(key=1)).drop('key', 1)
        final_df.columns = season_df_columns
        season_df = season_df.append(final_df, ignore_index = True)

    season_df.to_csv("{} Tip Off Results.csv".format(season), index = False)

    players_df = pd.DataFrame(columns = ['PlayerID','Name','Height','Birthday'])

    for p in players:
        name = players[p]['Name']
        height = players[p]['Height']
        bday = players[p]['Birthday']
        
        players_df = players_df.append(pd.DataFrame([[p,name,height,bday]], columns = players_df.columns), ignore_index = True)

    players_df.to_csv('{} Players Dictionary.csv'.format(season),index = False)