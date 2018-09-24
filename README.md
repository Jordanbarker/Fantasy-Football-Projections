# Fantasy-Football-Git

### Precaution: This is my first webscrapping/github project. I'm still making several changes

## The Basics
My league is located on http://fantasy.nfl.com so all of the functions are based around that.

Using python libraries such as Selenium and BeautifulSoup, I have created some functions to search websites and get weekly player projections.
The goal of the project is to make more accurate predictions on who to play week by week and possibly have players swapped automatically.

Here is a sample of what the function projectedScoresByTeam() returns:

| Player | Avg Proj | NFL | ESPN | FantasyPros | CBSSports | Yahoo |
| - | - | - | - | - | - | - |
| Cam Newton | 11.42 | 19.3 | 18.8 | 19 | 0 | 0 |
| Melvin Gordon | 14.64 | 14.5 | 14.2 | 13.4 | 14.8 | 16.3 |
| Christian McCaffrey | 9.26 | 14.1 | 18.7 | 13.5 | 0 | 0 |
| Golden Tate | 10.76 | 9.1 | 14.3 | 10 | 8.6 | 11.8 |

Some websites have very different projected scores, and I would like to investigate which is the most accurate at the end of the season.

This is a learning project so any input you have on how I can improve the project would be greatly appreciated!
