import requests
from bs4 import BeautifulSoup
import datetime as dt
import sys
#https://backoffice.lufttransport.no/indexStatic.php?static=scheduleStaticKingsBay&year=20&month=3

"""A script to parse the current schedule from Lufttransporten backoffice and select available flights to and from Ny-Ålesund, given some contraints.

Author: M.Buschmann
Date: 2020-02-22
"""

if len(sys.argv)==7:
    try:
        earliest_to_date = dt.datetime.strptime(sys.argv[1], '%Y%m%d')
        latest_return_date = dt.datetime.strptime(sys.argv[2], '%Y%m%d')
        daysstay = int(sys.argv[3])
        daysstaypm = int(sys.argv[4])
        earlyflightLYRNYA = False
        lateflightLYRNYA = False
        earlyflightNYALYR = False
        lateflightNYALYR = False
        if sys.argv[5]=='early':
            earlyflightLYRNYA = True
        elif sys.argv[5]=='late':
            lateflightLYRNYA = True
        else:
            raise(Exception('wrong argument'))
        if sys.argv[6]=='early':
            earlyflightNYALYR = True
        elif sys.argv[6]=='late':
            lateflightNYALYR = True
        else:
            raise(Exception('wrong argument'))
    except Exception as e:
        print(e)
        exit('... exited ...')
else:
    e = """
    Usage:\n\t
    python3 findflights.py <earliest LYR-NYA date (YYYYmmdd)> <latest NYA-LYR date (YYYYmmdd)> <number of days to stay> <pluminus days> <flight LYR-NYA (early|late)> <flight NYA-LYR (early|late)>
    """
    exit(e)

months = []
d = earliest_to_date
while d<=latest_return_date:
    months.append(d)
    if d.month==12:
        d = dt.datetime(d.year+1, 1,1)
    else:
        d = dt.datetime(d.year, d.month+1, 1)

new_table = []
for month in months:
    year = dt.datetime.strftime(month, '%y')
    mon = str(int(dt.datetime.strftime(month, '%m')))
    payload = {'static':'scheduleStaticKingsBay', 'year': year, 'month':mon}
    r = requests.get('https://backoffice.lufttransport.no/indexStatic.php', params=payload)
    soup = BeautifulSoup(r.content, 'lxml')
    tables = soup.find_all('table')
    for table in tables:
        for row in table.find_all('tr'):
            tablerow = []
            columns = row.find_all('td')
            for column in columns:
                c = column.get_text().strip()
                tablerow.append(c)
            if not len(tablerow)==0:
                new_table.append(tablerow)

flights = {'date':[], 'seats':[], 'from':[], 'to':[]}
for row in new_table:
    if 'production' in row[0]:
        srow = row[0].strip().strip(' production')
        date0 = dt.datetime.strptime(srow, '%Y-%m-%d')
    else:
        t = row[0]
        date = date0+dt.timedelta(hours=int(t[:2]), minutes=int(t[2:]))
        flights['date'].append(date)
        flights['from'].append(row[2])
        flights['to'].append(row[3])
        flights['seats'].append(int(row[4]))
flights['N'] = len(flights['date'])

isearlyflight = lambda t: True if t.hour<14 else False
islateflight = lambda t: True if t.hour>=14 else False

nmin, nmax = 0, flights['N']-1
for i in range(flights['N']):
    if flights['date'][i]>latest_return_date+dt.timedelta(days=1):
        nmax=i
        break
    else: pass
for i in range(flights['N']):
    if flights['date'][i]>=earliest_to_date:
        nmin=i
        break
    else: pass

to_flights_possible = []
for i in range(nmin,nmax):
    cond1 = flights['date'][i]+dt.timedelta(days=daysstay-daysstaypm)<=latest_return_date
    if earlyflightLYRNYA:
        cond2 = isearlyflight(flights['date'][i])
    elif lateflightLYRNYA:
        cond2 = islateflight(flights['date'][i])
    else:
        cond2 = True
    if cond1 and cond2:
        if flights['from'][i]=='LYR' and flights['to'][i]=='NYA':
            if flights['seats'][i]>=1:
                #print('\t------')
                #print('LYR - NYA ', flights['date'][i])
                to_flights_possible.append(flights['date'][i])

from_flights_possible = []
for i in range(nmin,nmax):
    cond1 = flights['date'][i]-dt.timedelta(days=daysstay+daysstaypm)<=latest_return_date
    if earlyflightNYALYR:
        cond2 = isearlyflight(flights['date'][i])
    elif lateflightNYALYR:
        cond2 = islateflight(flights['date'][i])
    else:
        cond2 = True
    if cond1 and cond2:
        if flights['from'][i]=='NYA' and flights['to'][i]=='LYR':
            if flights['seats'][i]>=1:
                #print('\t------')
                #print('NYA - LYR ', flights['date'][i])
                from_flights_possible.append(flights['date'][i])

print('\n#####################################\n')
for i in to_flights_possible:
    for j in from_flights_possible:
        cond1 = j>=i+dt.timedelta(days=daysstay-daysstaypm)
        cond2 = j<=i+dt.timedelta(days=daysstay+daysstaypm)
        if cond1 and cond2:
            #print('\t------')
            print('NYA - LYR ', i)
            print('LYR - NYA ', j, '\n')
        else: pass
print('\n#####################################\n')
