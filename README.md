# NBA-Tip-Off
Data on NBA tip off games to determine who will win the tip and who will score first.

# Details
- The CSV's that have "Bad Game" are games that didn't have the tip off data. It just stared with a team having the ball, so I don't know who the tip was between. I have excluded these games for now (only like 5 games out of 1230 each year
 
# How to query data
In the Main folder, you will see the NBA.db database. Using SQLite, you can open it and start to query it.

The two tables are called season_data and players.

If you want to see the headers of the columns when you query, when you open it up type in the command .headers on;. Everything else should be like regular SQL.

If you have any questions about downloading SQLite or how to run it, start here: https://www.sqlite.org/index.html. There are a lot of good tutorials and documentation of how to get started. 
