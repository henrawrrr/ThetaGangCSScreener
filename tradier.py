import config, requests

wlist = open('watchlist.txt', 'r')
stocks = wlist.readlines()
output = open('output.txt', 'w')
d = open('dates.txt', 'r')
dates = d.readlines()

GreedLimiter = 0.03 #limiter for ROC
Collatlimiter = 10000 #limiter for collat
thetalimiter = -0.3

for date in dates: 
    date = date.strip('\n')
    for stock in stocks:
        stock = stock.strip('\n')
        response = requests.get('https://sandbox.tradier.com/v1/markets/options/chains',
            params={'symbol': stock, 'expiration': date, 'greeks': 'true'},
            headers={'Authorization': 'Bearer {}'.format(config.ACCESS_TOKEN), 'Accept': 'application/json'}
        )
        opt_response = response.json()
        if response.status_code != 200:
            print("oh fuck error here on " + stock + " options")
        if opt_response is None or opt_response['options'] is None:
            print("No option chain on " + date)
        else:
            qresponse = requests.get('https://sandbox.tradier.com/v1/markets/quotes',
                params={'symbols': stock, 'greeks': 'false'},
                headers={'Authorization': 'Bearer {}'.format(config.ACCESS_TOKEN), 'Accept': 'application/json'}
            )
            q_response = qresponse.json()
            if qresponse.status_code != 200:
                print("oh fuck error here on " + stock + " quote")
            lastq = q_response['quotes']['quote']['last']
            for i in range(len(opt_response['options']['option'])):
                theta = opt_response['options']['option'][i]['greeks']['theta']
                otype = opt_response['options']['option'][i]['option_type']
                strike = opt_response['options']['option'][i]['strike']
                if theta <= -.3:
                    for j in range(len(opt_response['options']['option'])):
                        Ltheta = opt_response['options']['option'][j]['greeks']['theta']
                        Lotype = opt_response['options']['option'][j]['option_type']
                        Lstrike = opt_response['options']['option'][j]['strike']
                        dtheta = theta - Ltheta
                        dstrike = strike - Lstrike
                        if otype == Lotype and dtheta <= thetalimiter:
                            collat = dstrike * 100
                            olast = opt_response['options']['option'][i]['bid']
                            Llast = opt_response['options']['option'][j]['ask']
                            premium = abs(olast - Llast) * 100
                            ROC = premium / collat
                            if ROC >= GreedLimiter and collat <= Collatlimiter:
                                if otype == "put" and strike < lastq and dstrike > 0:
                                    a = opt_response['options']['option'][i]['description']
                                    b = opt_response['options']['option'][j]['description']
                                    output.write("PCS: " + str(a) + " " + str(b) + " theta: " + str(dtheta) + " Collat: " + str(collat) + " Premium: " + str(premium) + " ROC: " + str(ROC) + "\n")
                                elif otype == "call" and strike > lastq and dstrike < 0:
                                    a = opt_response['options']['option'][i]['description']
                                    b = opt_response['options']['option'][j]['description']
                                    output.write("CCS: " + str(a) + " " + str(b) + " theta: " + str(dtheta) + " Collat: " + str(collat) + " Premium: " + str(premium) + " ROC: " + str(ROC) + "\n")
print("done")
