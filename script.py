import requests as re
import pandas as pd
import numpy as np
import json
import argparse
import config
from urllib.parse import urljoin
import csv

class API:
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "User-Agent": "PostmanRuntime/7.29.2",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://worldtabletennis.com",
        "Referer": "https://worldtabletennis.com/"
    }

    def __init__(self, apiEndPoint, apiCredentials, method, **kwargs):
        self.apiEndPoint = apiEndPoint
        self.apiCredentials = apiCredentials
        self.method = method
        self.kwargs = kwargs
        self.appendAuthHeaders()

    def __str__(self):
        variablesConcatStr = ""
        for key, value in self.kwargs.items():
            variablesConcatStr = variablesConcatStr + "Key={}, Value={}\n".format(key, value)
        return f"API Endpoint: {self.apiEndPoint}\nAPI Key: {self.apiKey}\nVariables:\n{variablesConcatStr}"
    
    def appendAuthHeaders(self):
        if len(self.apiCredentials) < 128:
            self.headers["ApiKey"] = self.apiCredentials
        else:
            self.headers["Authorization"] = "Bearer " + self.apiCredentials
        return

    def fetch_data(self):
        data = {}
        for key, value in self.kwargs.items():
            data[key] = value
        json_data = data

        if self.method == "GET":
            res =re.get(
                url=self.apiEndPoint,
                headers=self.headers,
                params=json_data
            )
            if res.status_code == 200:
                return res.json()
            else:
                print("Failed calling API!")
                print(res.text)
                exit()
        elif self.method == "POST":
            res = re.post(
                url=self.apiEndPoint,
                headers=self.headers,
                json=json_data
            )
            if res.status_code == 200:
                return res.json()
            else:
                print("Failed calling API!")
                print(res.text)
                exit()
        

def getCountryCodeByCountryName(countryName=""):
    f = open("countries.json")
    countriesJSON = json.load(f)
    for i in range(len(countriesJSON)):
         if countriesJSON[i]["countryName"] == countryName.capitalize():
             countryCode = countriesJSON[i]["countryCode"]
             return countryCode
    return


def getCountryNameByCountryCode(countryCode=""):
    f = open("countries.json")
    countriesJSON = json.load(f)
    for i in range(len(countriesJSON)):
         if countriesJSON[i]["countryCode"] == countryCode.upper():
             countryName = countriesJSON[i]["countryName"]
             return countryName
    return


def convertDFtoCSV(df):
    pass
    return


def searchQuery(query="", boolSpecificRecord=True):
    if query == "":
        searchInput = input("Please enter search:")
    else:
        searchInput = query
    api = API(config.APIsearchPlayer, config.dictAPIkey[config.APIsearchPlayer], config.dictAPIMethod[config.APIsearchPlayer],searchText=searchInput)
    df = pd.json_normalize(api.fetch_data())
    if boolSpecificRecord == True:
        print(df[["ittfid", "nationality", "gender", "age", "fullName","ranking"]])
        chosenIndex = input("Please choose index of athlete to print out to csv:")
        if chosenIndex.isnumeric():
            print("Selected {} (ittfid={}). Printing out data...".format(df["fullName"][int(chosenIndex)], df["ittfid"][int(chosenIndex)]))
            return df.iloc[int(chosenIndex)]
    else:
        return df
    return


def getAllPlayers():
    api = API(config.APIgetAllPlayers, config.dictAPIkey[config.APIgetAllPlayers], config.dictAPIMethod[config.APIgetAllPlayers])
    df = pd.json_normalize(api.fetch_data()["Result"])
    print(df)
    return


def getPlayerNamesAndIttfid():
    api = API(config.APIgetPlayerWithNameList, config.dictAPIkey[config.APIgetPlayerWithNameList], config.dictAPIMethod[config.APIgetPlayerWithNameList])
    df = pd.json_normalize(api.fetch_data())
    print(df)
    return


def getPlayerStats(ittfid, StartDate="1900-10-10", EndDate="9999-12-31"):
    api = API(config.APIgetStatsByPlayers, config.dictAPIkey[config.APIgetStatsByPlayers], config.dictAPIMethod[config.APIgetStatsByPlayers], ittfid=ittfid, StartDate=StartDate, EndDate=EndDate)
    df = pd.json_normalize(api.fetch_data()["Result"])
    return df


def getEventsByYear(yearFilter="2023"):
    jsonArguments = "[{\"name\":\"StartDateTime\",\"value\":" + str(yearFilter) + ",\"custom_handling\":\"multimatch_year_or_filter\",\"condition\":\"or_start\"},{\"name\":\"FromStartDate\",\"value\":" + str(yearFilter) + ",\"custom_handling\":\"multimatch_year_or_filter\",\"condition\":\"or_end\"}]"
    api = API(config.APIgetEventsByDate, config.dictAPIkey[config.APIgetEventsByDate], config.dictAPIMethod[config.APIgetEventsByDate], custom_filter=jsonArguments)
    df = pd.json_normalize(api.fetch_data()[0]["rows"])
    print(df[['EventId', 'EventName', 'EventType', 'Country', 'City', 'StartDateTime', 'EndDateTime']])
    return


def getAllAthletesByCountry(countries_list=config.countries_list):
    if countries_list != config.countries_list:
        try:
            f = open(countries_list, "r")
            countries_list = list(csv.reader(f))
            f.close()
        except Exception as e:
            print(e)
            exit()
    print("Getting all athletes by country with list ({})...".format(countries_list))
    df = pd.DataFrame()
    for country in countries_list:
        df_country = searchQuery(country, boolSpecificRecord=False)
        df = pd.concat([df, df_country])
    return df


def getEventDocCodeByEventID(eventID):
    print("Querying Event Doc Code by Event ID...")
    req = re.models.PreparedRequest()
    req.prepare(url=config.APIgetEventDocCode, params={"EventId": eventID, "DocumentCode": "TTE"})
    api = API(req.url, config.dictAPIkey[config.APIgetEventDocCode], config.dictAPIMethod[config.APIgetEventDocCode])
    df = pd.json_normalize(api.fetch_data())
    print(df)
    return


def getDetailedResultsByEventIDandEventDocCode(eventID, eventDocCode, eventName=""):
    print("Getting Detailed Results for Event ({}, ID:{})...".format(eventName, eventID))
    req = re.models.PreparedRequest()
    req.prepare(url=urljoin(config.APIgetDetailedResultsByEvent, eventID + '/' + eventDocCode), params={"require_full_msg": "true"})
    api = API(req.url, config.dictAPIkey[config.APIgetDetailedResultsByEvent], config.dictAPIMethod[config.APIgetDetailedResultsByEvent])
    res = api.fetch_data()
    df = pd.json_normalize(res)
    df_competitors = pd.json_normalize(res['competitiors'])
    print(df)
    print(df_competitors)
    print(getPlayersNamesJSON(df_competitors))
    return


def getPlayersNamesJSON(df_competitors):
    players = {}
    try:
        for i in range(len(df_competitors)):
            df_teams = pd.json_normalize(df_competitors['players'][i])
            for player in range(len(df_teams)):
                players[df_teams['playerId'][player]] = df_teams['playerName'][player]
        return players
    except Exception as e:
        print(e)
        exit()


def getResultsOfAllAthletesDF(df):
    for i in range(len(df)):
        pass
    return


def getStatsOfAllAthletesDF(df_allAthletes=pd.DataFrame()):
    df_stats = pd.DataFrame()
    for i in range(len(df_allAthletes)):
        print(df_allAthletes.iloc[i]['ittfid'])
        playerStats = getPlayerStats(ittfid=df_allAthletes.iloc[i]['ittfid'])
        df_stats = pd.concat([df_stats, playerStats])
    return df_stats


def outputDFtoCSV(df=pd.DataFrame(), outputFileName=config.outputCSVFileName):
    df.to_csv(outputFileName, index=False)
    return


def outputDFtoXLSX(df=pd.DataFrame(), outputFileName=config.outputXlsxFileName):
    writer = pd.ExcelWriter(outputFileName, engine="openpyxl")
    df.to_excel(writer, index=False)
    return


def filterNames(namelistCSV=config.namelistCSV):
    try:
        df_namelist = pd.read_csv(namelistCSV)
    except Exception as e:
        print(e)
        exit()
    
    return

def parseScriptArguments():
    description = "This is a python script to automate data collection and cleaning of World Athletics results retrieved from World Athletics website's backend API."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-ath", "--Athlete", help="Define Athlete for Search")
    parser.add_argument("-disc", "--Discipline", help="Define Discipline for Search")
    parser.add_argument("-o", "--OutputName", help="Define Output file name of Scrapped Results (without '.xlsx' extension)")
    parser.add_argument("-tf", "--TargetFileName",
                        help="Target File Name (default is cleanedResults.csv) for performing filtering operations on using namelist.csv and discipline supplied. Please include '.csv' extension in argument.")
    parser.add_argument("-nl", "--NameListCSV",
                        help="Name List CSV file (default is namelist.csv) that will be used for performing filtering operations on cleaned results data. Please include '.csv' extension in argument and ensure '* namelist.csv' naming convention.")
    parser.add_argument("-c", "--CompileIntoFolder", action='store_true',
                        help="Compile filtered namelist CSV and filtered data into a folder specified by user. Please ensure argument is a legal folder name.")
    parser.add_argument("-filteronly", "--FilterOnly", action='store_true',
                        help="Filter existing cleanedResults.csv by discipline specified. Scrapping will not be performed prior.")
    parser.add_argument("-scrapeonly", "--ScrapeOnly", action='store_true',
                        help="Scape and clean data only. Will not perform filtering by discipline or namelist.csv.")
    parser.add_argument("-search", "--SearchAthlete", action='store_true',
                        help="Search athlete using API and return results as searchResults.csv.")
    parser.add_argument("-append", "--AppendToCleanedResults", action='store_true',
                        help="Append search results to cleanedResults.csv.")
    parser.add_argument("-athCSV", "--AthleteCSV", help="Define Athlete CSV file for searches.")
    parser.add_argument("-countryCSV", "--countryCSV", help="Define Country CSV file for searches and scrapping.")
    args = parser.parse_args()

    return


def main():
    config.importAPIs()
    print(getStatsOfAllAthletesDF(getAllAthletesByCountry()))
    return


if __name__ == "__main__":
    main()