from bs4 import BeautifulSoup
import pandas as pd
import requests
from selenium import webdriver
import re
import time


# Starts chrome webdriver
def startChromeDriver(executable_path):
    driver = webdriver.Chrome(executable_path)
    return driver

# Log into nfl.com, returns leagueID
def loginToNflLeague(driver, leagueID username, password):
    driver.get("https://www.nfl.com/login?s=fantasy&returnTo=http%3A%2F%2Ffantasy.nfl.com%2Fleague%2F" + leagueID)
    driver.find_element_by_id("fanProfileEmailUsername").send_keys(username)
    driver.find_element_by_id("fanProfilePassword").send_keys(password)
    driver.find_element_by_xpath("//*[@id='content']/div/div/div[2]/div[1]/div/div[3]/div[2]/main/div/div[2]/div[2]/form/div[3]/button").click()
    time.sleep(1)
    return re.split("/", driver.current_url)[4]

# Puts league table into a dataframe
def pullLeagueTable(driver, leagueID):
    driver.get("http://fantasy.nfl.com/league/" + leagueID)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find('table').find('tbody')    
    
    # Copy table body
    rank = []
    team = []
    wlt = []
    pct = []
    stk = []
    waiver = []
    pointsFor = []
    pointsAgainst = []
    for row in table.findAll('tr'):
        cells = row.findAll('td')
        
        teamNum = re.search(r'\d+', str(cells[0].find('span'))).group()
        driver.find_element_by_xpath('//a[@href="/league/' + leagueID + '/team/' + teamNum + '"]').click()
        soup2 = BeautifulSoup(driver.page_source, "html.parser")
        actualName = soup2.findAll('li')[0].find(text=True)
        driver.execute_script("window.history.go(-1)")    
        teamName = cells[1].findAll('a')[1].find(text=True)
        teamNew = teamName + " (" + actualName + ")"
        team.append(teamNew)
        
        rank.append(cells[0].find(text=True))
        wlt.append(cells[2].find(text=True))
        pct.append(cells[3].find(text=True))
        stk.append(cells[4].find(text=True))
        waiver.append(cells[5].find(text=True))
        pointsFor.append(cells[6].find(text=True))
        pointsAgainst.append(cells[7].find(text=True))
    
    # Create dataframe of table
    df=pd.DataFrame(rank, columns=['Rank'])
    df['Team'] = team
    df['W-L-T'] = wlt
    df['Pct'] = pct
    df['Stk'] = stk
    df['Waiver'] = waiver
    df['For'] = pointsFor
    df['Against'] = pointsAgainst
    df.set_index('Rank', inplace=True)
    return df

def getProjectedScoresByTeam(driver, leagueID, teamNumber, projweek, CBSPlayerNums = 0):
    playerNames = []
    avgproj = []
    NFLproj = []
    ESPNproj = []
    FPproj = []
    CBSproj = []
    Yahooproj = []
    espn = "http://games.espn.com/ffl/tools/projections?avail=-1&search=" #cam%20newton
    fantasypros = "https://www.fantasypros.com/nfl/players/"              #cam-newton.php
    cbssports = "https://www.cbssports.com/fantasy/football/players/"     #1273186/cam-newton/    
    yahoo1 = "https://football.fantasysports.yahoo.com/f1/74419/playersearch?&search=" #cam%20newton
    yahoo2 = "&stat1=S_PW_" + projweek + "&jsenabled=1"
    driver.get("http://fantasy.nfl.com/league/" + str(leagueID) + "/team/" 
               + teamNumber + "#teamHome=teamHome%2C%2Fleague%2F" + leagueID "%2Fteam%2F6%253FstatCategory%253DprojectedStats%2526week%253D3%2Creplace")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find('table').find('tbody')    
    for row in table.findAll('tr'):
        cells = row.findAll('td')
        if len(cells)>3:
            playerNames.append(cells[2].find(text=True))
            NFLproj.append(round(float(cells[17].find(text=True)), 1))

    for name in playerNames:
        #espn
        site = requests.get(espn + name.replace(" ", "%20"))
        soup = BeautifulSoup(site.text, "html.parser")
        ESPNproj.append(soup.find(class_='playertableStat appliedPoints sortedCell').find(text=True))

        #fantasypros
        site = requests.get(fantasypros + name.replace(" ", "-").lower() + ".php")
        soup = BeautifulSoup(site.text, "html.parser")
        FPproj.append(soup.findAll(class_='pull-right')[9].find(text=True).split()[0])

        #cbssports
        if(CBSPlayerNums == 0):
            driver.get(cbssports)
            driver.find_element_by_id("s2id_autogen1").send_keys(name)
            driver.find_element_by_xpath("//*[@id='player-search']/div[2]/button/span").click()
            driver.find_element_by_xpath("//*[@id='tab-content-1']/section/div/div/div[3]/table/tbody/tr/td[1]/a/div").click()
            soup = BeautifulSoup(driver.page_source, "html.parser")
            CBSproj.append(soup.findAll('table')[0].find('tbody').findAll('tr')[int(projweek)-1].findAll('td')[1].find(text=True))
        else:
            site = requests.get(cbssports + CBSPlayerNums[name] + "/" + name.replace(" ", "-").lower())
            soup = BeautifulSoup(site.text, "html.parser")
            soup = str(soup.find(class_="marquee-full-pinch marquee-full-overlay"))
            soup = re.split(r"[\[\]]", soup[180:571])
            soup = [x for x in soup if x.startswith('\\')]
            CBSproj.append(re.split(',', soup[int(projweek)-1])[1])

        #YahooSports
        site = requests.get(yahoo1 + name.replace(" ", "%20").lower() + yahoo2)
        soup = BeautifulSoup(site.text, "html.parser")
        soup = soup.findAll('table')[1].find('tbody').find(class_='Fw-b').find(text=True)
        Yahooproj.append(round(float(soup), 1))

    for num in range(len(NFLproj)):
        avg = (float(NFLproj[num]) + float(ESPNproj[num]) + float(FPproj[num])
               + float(CBSproj[num]) + float(Yahooproj[num]))/5
        avgproj.append(avg)

    allProjections=pd.DataFrame(playerNames, columns=['Player'])
    allProjections['AVG Proj'] = avgproj
    allProjections['NFL']=NFLproj
    allProjections['ESPN']=ESPNproj
    allProjections['Fantasypros']=FPproj
    allProjections['CBSSports']=CBSproj
    allProjections['Yahoo']=Yahooproj
    return allProjections     
    
# Returns player names by team number
def getPlayerNamesByTeam(driver, leagueID, teamNumber):
    driver.get("http://fantasy.nfl.com/league/" + leagueID + "/team/" + teamNumber)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find('table').find('tbody')
    playerNames = []
    #NFLproj = []
    
    for row in table.findAll('tr'):
        cells = row.findAll('td')
        if len(cells)>3:
            playerNames.append(cells[2].find(text=True))
            #NFLproj.append(round(float(cells[17].find(text=True)), 1))
    return playerNames 

# Returns a dataframe of websites projected scores
def getProjectedScores(playerNames, projweek, NFLproj, CBSPlayerNums = 0): 
    espn = "http://games.espn.com/ffl/tools/projections?avail=-1&search=" #cam%20newton
    fantasypros = "https://www.fantasypros.com/nfl/players/"              #cam-newton.php
    cbssports = "https://www.cbssports.com/fantasy/football/players/"     #1273186/cam-newton/
    
    EPSNproj = []
    FPproj = []
    CBSproj = []
    Yahooproj = []

    for name in A:
        #espn
        site = requests.get(espn + name.replace(" ", "%20"))
        soup = BeautifulSoup(site.text, "html.parser")
        ESPNproj.append(soup.find(class_='playertableStat appliedPoints sortedCell').find(text=True))
        
        #fantasypros
        site = requests.get(fantasypros + name.replace(" ", "-").lower() + ".php")
        soup = BeautifulSoup(site.text, "html.parser")
        FPproj.append(soup.findAll(class_='pull-right')[9].find(text=True).split()[0])
        
        #cbssports
        if(CBSPlayerNums == 0):
            driver.get(cbssports)
            driver.find_element_by_id("s2id_autogen1").send_keys(name)
            driver.find_element_by_xpath("//*[@id='player-search']/div[2]/button/span").click()
            driver.find_element_by_xpath("//*[@id='tab-content-1']/section/div/div/div[3]/table/tbody/tr/td[1]/a/div").click()
            soup = BeautifulSoup(driver.page_source, "html.parser")
            CBSproj.append(soup.findAll('table')[0].find('tbody').findAll('tr')[projweek-1].findAll('td')[1].find(text=True))
        else:
            site = requests.get(cbssports + CBSnums[name] + "/" + name.replace(" ", "-").lower())
            soup = BeautifulSoup(site.text, "html.parser")
            soup = str(soup.find(class_="marquee-full-pinch marquee-full-overlay"))
            soup = re.split(r"[\[\]]", soup[180:571])
            soup = [x for x in soup if x.startswith('\\')]
            CBSproj.append(re.split(',', soup[projweek-1])[1])
        
        #yahooSports
        if(YahooPlayerNums == 0):
            YahooPlayerNums.append(0)
        else:
            YahooPlayerNums.append(0)
    
    allProjections=pd.DataFrame(playerNames, columns=['Player'])
    allProjections['NFL']=NFLproj
    allProjections['ESPN']=ESPNproj
    allProjections['Fantasypros']=FPproj
    allProjections['CBSSports']=CBSproj
    allProjections['Yahoo']=Yahooproj
    
    return allProjections

# Returns a dictionary in the following format {"Cam Newton":1273186}
def getCBSPlayerNumbers(driver, playernames):
    playernums = {}
    for name in playerNames:
        driver.get("https://www.cbssports.com/search/football/players/")
        driver.find_element_by_id("s2id_autogen1").send_keys(name)
        driver.find_element_by_xpath("//*[@id='player-search']/div[2]/button/span").click()
        driver.find_element_by_xpath("//*[@id='tab-content-1']/section/div/div/div[3]/table/tbody/tr/td[1]/a/div").click()
        playernums[name] = (re.split("/", driver.current_url)[6])
    return playernums

# Got ahead of myself making this one 
# Not really useful since the yahoo player page does not have projections
# Returns a dictionary in the following format {"Cam Newton":1273186}
def getYahooPlayerNumbers(driver, playerNames):
    playernums = {}
    driver.get("https://football.fantasysports.yahoo.com/f1/playertradessearch")
    for name in playerNames:
        driver.find_element_by_id("playersearchtext").send_keys(name)
        driver.find_element_by_xpath("//input[@value='Find Player']").click()
        driver.find_element_by_class_name("F-link").click()
        driver.switch_to_window(driver.window_handles[1])
        playernums[name] = re.split("/", driver.current_url)[5]
        driver.close()
        driver.switch_to_window(driver.window_handles[0])
    return playernums
