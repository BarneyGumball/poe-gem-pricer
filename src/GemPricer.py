import urllib
import urllib2
import requests
import json
import re
import time

# MODIFY THESE FOR YOUR OWN ACCOUNT

MINIMUM_GEM_PRICE = 1.5                         # minimum average price in chaos for a gem to be displayed
ACCOUNT_NAME = 'My_Username'                    # log in username
POESESSID = '32charstringthatyoufindinbrowser'  # log in to pathofexile.com and view the page cookies (f12 in chrome), put the POESESSID cookie here
LEAGUE_NAME = 'Standard'                        # league name to search tabs by
TAB_INDEX = '11'                                # count the amount of tabs to the left of your gem tab (don't include the gem tab
                                                # in your count), this is the TAB_INDEX

# UPDATE THESE CURRENCY VALUES IN TERMS OF CHAOS

DIVINE_VALUE = 12
EXALT_VALUE = 65
VAAL_VALUE = 1
GCP_VALUE = 1

#constants

STASH_API = 'https://www.pathofexile.com/character-window/get-stash-items'
POE_TRADE = 'http://poe.trade/search'
ageIgnoreList = {'week', 'month'}
pricePattern = r"data-buyout=\"(.*?)\""
priceRE = re.compile(pricePattern)
accNamePattern = r"data-seller=\"(.*?)\""
accNameRE = re.compile(accNamePattern)
qualityPattern = r"data-quality=\"(.*?)\""
qualityRE = re.compile(qualityPattern)
levelPattern = r"data-level=\"(.*?)\""
levelRE = re.compile(levelPattern)
agePattern = r"found-time-ago\">(.*?)</span>"
ageRE = re.compile(agePattern)

def getStash():
    print 'Getting stash...'
    options = {'accountName' : ACCOUNT_NAME,
               'tabIndex' : TAB_INDEX,
               'league' : LEAGUE_NAME,
               'tabs' : '0'}
    data = urllib.urlencode(options)
    cookie_val = 'POESESSID=' + POESESSID
    header = {'Cookie' : cookie_val}
    req = urllib2.Request(STASH_API, data, header)
    response = urllib2.urlopen(req)
    jsonresp = json.load(response)
    print 'Stash Acquired.\n'
    return jsonresp['items']

def getGems(stash):
    print 'Processing gems...'
    gemlist = {}
    for obj in stash:
        if 'gems' in obj['category']:
            gemname = obj['typeLine']
            qual = 0
            for prop in obj['properties']:
                if(prop['name'] == 'Quality'):
                    qual = prop['values'][0][0][1:-1]
            # handle duplicate gem names
            if gemname in gemlist:
                gemlist[gemname].append(qual)
            else:
                gemlist[gemname] = [qual]
    print 'Gems processed.\n'
    return gemlist

def doSearch(payloadOptions):
    payload = {'league': LEAGUE_NAME,
               'type': 'Gem',
               'online': 'x',
               'capquality': 'x'}

    payload.update(payloadOptions)
    return requests.get(POE_TRADE, data=payload)

def getBlock(i, r):
    return re.search(r"<tbody id=\"item-container-" + str(i) + r"\"(.*?)<\/tbody>", r.text, re.DOTALL)

def createTradeList(req):
    idx = 0
    itemBlock = getBlock(idx, req)
    tradeList = []

    while(itemBlock):
        #ignore old listings
        itemAge = ageRE.search(itemBlock.group(0)).group(1)
        skipItem = False
        for s in ageIgnoreList:
            if s in itemAge:
                skipItem = True
                break
        if skipItem:
            idx += 1
            itemBlock = getBlock(idx, req)
            continue

        #make new dict and add to list
        newEntry = {'name': gem}
        newEntry['price'] = priceRE.search(itemBlock.group(0)).group(1)
        newEntry['accName'] = accNameRE.search(itemBlock.group(0)).group(1)
        newEntry['quality'] = qualityRE.search(itemBlock.group(0)).group(1)
        newEntry['level'] = levelRE.search(itemBlock.group(0)).group(1)
        newEntry['age'] = itemAge

        tradeList.append(newEntry)

        idx += 1
        itemBlock = getBlock(idx, req)

    return tradeList

def printGem(gemDict):
    print('Gem: ' + str(gemDict['name']) + ', +' + str(gemDict['quality']) + '%, ' + str(gemDict['price']) + ', ' + str(gemDict['age']))

def checkGemPrice(gemname, gemquality):
    newRequest = doSearch({'q_min': gemquality, 'name': gemname})
    newList = createTradeList(newRequest)
    #get first 10 listings and check average is above MINIMUM_GEM_PRICE
    valueCount = 0
    averageChaos = 0
    #manually convert expensive listings into chaos equivalent
    for listing in newList[:10]:
        if 'divine' in listing['price']:
            valueCount += 1
            averageChaos += float(listing['price'].split(' ')[0]) * DIVINE_VALUE
        if 'exa' in listing['price']:
            valueCount += 1
            averageChaos += float(listing['price'].split(' ')[0]) * EXALT_VALUE
        if 'chaos' in listing['price']:
            valueCount += 1
            averageChaos += float(listing['price'].split(' ')[0])
        if 'vaal' in listing['price']:
            valueCount += 1
            averageChaos += float(listing['price'].split(' ')[0]) * VAAL_VALUE
        if 'gcp' in listing['price']:
            valueCount += 1
            averageChaos += float(listing['price'].split(' ')[0]) * GCP_VALUE
    if valueCount < 3:
        return False
    averageChaos = float(averageChaos) / float(valueCount)
    if averageChaos < MINIMUM_GEM_PRICE:
        return False
    print('Your Gem: ' + str(gemname) + ', +' + str(gemquality) + '%\n')
    chaosOnly = []
    for listing in newList:
        if 'chaos' in listing['price']:
            chaosOnly.append(listing)
    for listing in chaosOnly[:6]:
        printGem(listing)
    print ''
    return True



if __name__ == '__main__':
    stash = getStash()
    gemlist = getGems(stash)
    
    print 'Beginning poe.trade scraping and price comparisons...\n'
    for gem, gemquals in gemlist.iteritems():
        for gemqual in gemquals:
            if checkGemPrice(gem, gemqual):
                lowerQual = int(gemqual) - 2
                checkGemPrice(gem, str(lowerQual))
            time.sleep(2)
    print 'All gems price checked.'
