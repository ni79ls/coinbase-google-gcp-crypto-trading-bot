import firebase_admin
from firebase_admin import firestore

# Will automatically pull credentials from environment variable
firebase_admin.initialize_app() 

def cb_pub_connect(url, *args, **kwargs):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Establishes a connection to the public coinbase API with the given URL and arguments

    import requests
    from urllib.error import HTTPError
    try:
        if kwargs.get('param', None) is not None:
            params = kwargs.get('param')
            response = requests.get(url,params)
        else:
            response = requests.get(url)
        response.raise_for_status()
        print(f'HTTP connection {url} successful!')
        return response
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        #return http_err
    except Exception as err:
        print(f'Other error occurred: {err}')
        #return err

def cb_auth_get_connect(url_path, *args, **kwargs):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Establishes an authenticated connection to the coinbase API with the given URL, limit and cursor

    import hmac
    import hashlib
    import requests
    import time
    import json
    import os
    from urllib.error import HTTPError
    CB_API_KEY = os.environ.get('API_KEY')
    CB_SECRET_KEY = os.environ.get('API_SECRET')
    url_prefix = 'https://coinbase.com'
    url = url_prefix + url_path
    secret_key = CB_SECRET_KEY
    api_key = CB_API_KEY
    timestamp = str(int(time.time()))
    method = 'GET'
    body = ''
    if kwargs.get('body', None) is not None:
            body = kwargs.get('body')
            body = json.dumps(body)
    message = timestamp + method + url_path.split('?')[0] + body
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).digest()
    headers = {'accept': 'application/json',
        'CB-ACCESS-SIGN':signature.hex(),
        'CB-ACCESS-KEY':api_key,
        'CB-ACCESS-TIMESTAMP': timestamp}
    try:
        if kwargs.get('param', None) is not None:
            params = kwargs.get('param')
            response = requests.get(url, params, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f'HTTP connection {url} successful!')
        return response
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        #return http_err
    except Exception as err:
        print(f'Other error occurred: {err}')
        #return err

def cb_auth_post_connect(url_path, *args, **kwargs):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Establishes an authenticated connection to the coinbase API with the given URL, limit and cursor

    import hmac
    import hashlib
    import requests
    import time
    import os
    from urllib.error import HTTPError
    import json
    CB_API_KEY = os.environ.get('API_KEY')
    CB_SECRET_KEY = os.environ.get('API_SECRET')
    url_prefix = 'https://coinbase.com'
    url = url_prefix + url_path
    secret_key = CB_SECRET_KEY
    api_key = CB_API_KEY
    timestamp = str(int(time.time()))
    method = 'POST'
    body = ''
    if kwargs.get('body', None) is not None:
        body = kwargs.get('body')
    message = timestamp + method + url_path.split('?')[0] + json.dumps(body)
    signature = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).digest()
    headers = {'accept': 'application/json',
        'CB-ACCESS-SIGN':signature.hex(),
        'CB-ACCESS-KEY':api_key,
        'CB-ACCESS-TIMESTAMP': timestamp}
    try:
        if kwargs.get('param', None) is not None:
            params = kwargs.get('param')
            response = requests.post(url, params, headers=headers, json=body)
        else:
            response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        print(f'HTTP connection {url} successful!')
        return response
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        #return http_err
    except Exception as err:
        print(f'Other error occurred: {err}')
        #return err

def cb_get_product_info(product_id):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Returns basic product related information for the given product_id

    import json
    product = json.loads(cb_pub_connect(f'https://api.exchange.coinbase.com/products/{product_id}').text)
    return product

def cb_get_server_time():

    # Version: 1.00
    # Last Updated: Feb-06-2023
    # Returns the current time of the server as datetime (typically UK timezone).

    from datetime import datetime
    import json
    server_time = json.loads(cb_pub_connect('https://api.exchange.coinbase.com/time').text)
    return datetime.fromisoformat(server_time['iso'].replace('T', ' ', 1)[0:19])

def cb_get_24h_data(quote_currency, crypto_currencies):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Returns a pandas dataframe which contains one row per chosen crypto currency
    # For each currency, basic information such as open, high, low, volume is returned
    # in the given quote currency (e.g. EUR or USD).

    import pandas as pd
    import json
    currency_rows = []
    for currency in crypto_currencies:
        data = json.loads(cb_pub_connect('https://api.exchange.coinbase.com/products/'+currency+'-'+quote_currency+'/stats').text)
        currency_rows.append(data)
    df_24h_data = pd.DataFrame(currency_rows, index = crypto_currencies)
    df_24h_data['base_currency'] = df_24h_data.index
    df_24h_data['quote_currency'] = quote_currency
    df_24h_data['product_id'] = df_24h_data['base_currency']+'-'+df_24h_data['quote_currency']
    #df_24h_data['open'] = df_24h_data['open'].astype(float)
    #df_24h_data['high'] = df_24h_data['high'].astype(float)
    #df_24h_data['low'] = df_24h_data['low'].astype(float)
    #df_24h_data['volume'] = df_24h_data['volume'].astype(float)
    df_24h_data['last'] = df_24h_data['last'].astype(float)
    #df_24h_data['volume_30day'] = df_24h_data['volume_30day'].astype(float)
    #df_24h_data['performance'] = ((df_24h_data['last']-df_24h_data['open']) / df_24h_data['open']) * 100
    
    return df_24h_data

def cb_get_last_buy_fill_date(product_id):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Returns the date of the last settled buy order for the given product id.
    # In case no settled buy order is found, None is returned. 

    from datetime import datetime
    import pandas as pd
    try:
        #fills_gen = cbp_client.get_fills(product_id)
        #all_fills = list(fills_gen)
        df_fills = cb_get_aggregated_fills(product_id)
        df_fills = df_fills.sort_values(['date'], ascending=False) #newest to oldest
        df_fills = df_fills.query('side == \'BUY\' and trade_type == \'FILL\'').head(1)
        last_fill_date = df_fills['date'].iloc[0]
        # Must remove timezone awareness to do a comparison in the investment decision later on
        last_fill_date = datetime.fromisoformat(str(last_fill_date)).replace(tzinfo=None)
        return last_fill_date
    except:
        return None


def cb_get_fills(product_id='', order_id=''):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Returns a pandas dataframe which contains all fills. One line per fill
    # Optionally, can pass the product_id (like BTC-EUR)

    import json
    import pandas as pd
    # Attention: unlike with other Coinbase calls, the json does not return a has_next parameter!
    has_next = True
    cursor = ''
    lst_fills = []
    url_path = '/api/v3/brokerage/orders/historical/fills'
    try:
        while has_next:
            #params = {'limit':200, 'cursor':cursor, 'product_id':product_id, 'order_id':order_id}
            params = {'limit':200, 'cursor':cursor, 'product_id':product_id, 'order_id':order_id}
            response = cb_auth_get_connect(url_path=url_path, param = params)
            json_fills = json.loads(response.text)
            tmp_df_fills = pd.json_normalize(json_fills, record_path =['fills'])
            tmp_lst_fills = tmp_df_fills.values.tolist() 
            lst_fills.extend(tmp_lst_fills)
            cursor = json_fills['cursor']
            if cursor == '':
                has_next = False
        df_fills = pd.DataFrame(lst_fills)
        df_fills.columns = tmp_df_fills.columns.values.tolist()
        return df_fills
    except:
        return None

def cb_get_aggregated_fills(product_id='', order_id=''):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Returns a pandas dataframe which contains all fills in a nicer aggregated way.
    # One line per fill. Optionally, can pass the product_id (like BTC-EUR)

    import pandas as pd
    df_fills = cb_get_fills(product_id=product_id, order_id=order_id)
    try:
        df_fills['price'] = df_fills['price'].astype(float)
        df_fills['size'] = df_fills['size'].astype(float)
        df_fills['commission'] = df_fills['commission'].astype(float)
        df_fills['total_price'] = df_fills['size'] + df_fills['commission']
        df_fills['date'] = pd.to_datetime(df_fills['trade_time']).dt.floor('Min')
        df_fills_agg = df_fills.groupby(['order_id','trade_type','product_id','price','size_in_quote', 'side', 'date'], as_index =False)[['size','commission','total_price']].sum()
        return df_fills_agg
    except:
        return None

def cb_get_historic_data(start_date, end_date, interval, base_currency, quote_currency):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Returns a pandas dataframe with historic information for the given currency and interval

    import json
    VALID_INTERVAL = {'DAILY', '60MIN', '15MIN', '1MIN'}
    if interval not in VALID_INTERVAL:
        raise ValueError("results: interval must be one of %r." % VALID_INTERVAL)
    if interval == '1MIN':
        granularity = '60'
    elif interval == '15MIN':
        granularity = '900'
    elif interval == '60MIN':
        granularity = '3600'
    else: # DAILY as the default
        granularity = '86400'
    params = {'start':start_date, 'end':end_date, 'granularity':granularity}
    data = json.loads(cb_pub_connect('https://api.exchange.coinbase.com/products/'+quote_currency+'-'+base_currency+'/candles',
        param = params).text)
    [x.append(quote_currency) for x in data]
    [x.append(interval) for x in data]
    return data

def cb_get_enhanced_history(quote_currency, crypto_currencies):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Returns a pandas dataframe with time-sliced information about the choosen crypto currencies
    # One line in the dataframe represents one time-slice per currency.

    from datetime import timedelta
    import pandas as pd
    import numpy as np
    GRANULARITIES = ['DAILY','60MIN','15MIN','1MIN']
    currency_history_rows = []
    for currency in crypto_currencies:
        end_date = cb_get_server_time()
        # 1 minutes data:
        ##start_date = (end_date - timedelta(hours=2)).isoformat()
        ##currency_history_rows.extend(cb_get_historic_data(start_date,end_date,'1MIN', quote_currency, currency))
        # 15 minutes data:
        ##start_date = (end_date - timedelta(hours=75)).isoformat()
        ##currency_history_rows.extend(cb_get_historic_data(start_date,end_date,'15MIN', quote_currency, currency))
        # 60 minutes data:
        ##start_date = (end_date - timedelta(hours=300)).isoformat()
        ##currency_history_rows.extend(cb_get_historic_data(start_date,end_date,'60MIN', quote_currency, currency))
        # Daily data:
        start_date = (end_date - timedelta(days=90)).isoformat()
        currency_history_rows.extend(cb_get_historic_data(start_date,end_date,'DAILY', quote_currency, currency))
    df_history = pd.DataFrame(currency_history_rows)
    # Add column names in line with the Coinbase documentation
    df_history.columns = ['time','low','high','open','close','volume','base_currency','granularity']
    # We will add a few more columns just for better readability
    df_history['quote_currency'] = quote_currency
    df_history['date'] = pd.to_datetime(df_history['time'], unit='s')
    df_history['year'] = pd.DatetimeIndex(df_history['date']).year
    df_history['month'] = pd.DatetimeIndex(df_history['date']).month
    df_history['day'] = pd.DatetimeIndex(df_history['date']).day
    df_history['hour'] = pd.DatetimeIndex(df_history['date']).hour
    df_history['minute'] = pd.DatetimeIndex(df_history['date']).minute

    #AVERAGE_TRUE_RANGE_PERIODS = 14
    currency_history_rows_enhanced = []
    for currency in crypto_currencies:
        for granularity in GRANULARITIES:
            df_history_currency = df_history.query('granularity == @granularity & base_currency == @currency').copy()
            # Oldest to newest date sorting needed for SMA calculation
            df_history_currency = df_history_currency.sort_values(['date'], ascending=True)
            df_history_currency['SMA20'] = df_history_currency['close'].rolling(window=20).mean()
            df_history_currency['SMA20_std'] = df_history_currency['close'].rolling(window=20).std()
            df_history_currency['bb_low'] =  df_history_currency['SMA20'] - 2 * df_history_currency['SMA20_std']
            df_history_currency['bb_up'] =  df_history_currency['SMA20'] + 2 * df_history_currency['SMA20_std']
            #df_history_currency['SMA3'] = df_history_currency['close'].rolling(window=3).mean()
            #df_history_currency['SMA7'] = df_history_currency['close'].rolling(window=7).mean()
            #df_history_currency['EMA12'] = df_history_currency['close'].ewm(span=12, adjust=False).mean()
            #df_history_currency['EMA26'] = df_history_currency['close'].ewm(span=26, adjust=False).mean()
            #df_history_currency['MACD'] = df_history_currency['EMA12'] - df_history_currency['EMA26']
            #df_history_currency['MACD_signal'] = df_history_currency['MACD'].ewm(span=9, adjust=False).mean()
            #df_history_currency['macd_histogram'] = ((df_history_currency['MACD']-df_history_currency['MACD_signal']))
            #df_history_currency['open_to_close_perf'] = ((df_history_currency['close']-df_history_currency['open']) / df_history_currency['open'])
            #df_history_currency['high_low_diff'] = (df_history_currency['high']-df_history_currency['low'])
            #df_history_currency['high_prev_close_abs'] = np.abs(df_history_currency['high'] - df_history_currency['close'].shift())
            #df_history_currency['low_prev_close_abs'] = np.abs(df_history_currency['low'] - df_history_currency['close'].shift())
            #df_history_currency['true_range'] = df_history_currency[['high_low_diff', 'high_prev_close_abs', 'low_prev_close_abs']].max(axis=1)
            #df_history_currency['average_true_range'] = df_history_currency['true_range'].ewm(alpha=1/AVERAGE_TRUE_RANGE_PERIODS, min_periods=AVERAGE_TRUE_RANGE_PERIODS, adjust=False).mean()
            #df_history_currency['high_low_perf'] = ((df_history_currency['high']-df_history_currency['low']) / df_history_currency['high'])
            #df_history_currency['open_perf_last_3_period_abs'] = df_history_currency['open'].rolling(window=4).apply(lambda x: x.iloc[1] - x.iloc[0])
            #df_history_currency['open_perf_last_3_period_per'] = df_history_currency['open'].rolling(window=4).apply(lambda x: (x.iloc[1] - x.iloc[0])/x.iloc[0])
            #df_history_currency['bull_bear'] = np.where(df_history_currency['macd_histogram']< 0, 'Bear', 'Bull')
            currency_history_rows_enhanced.append(df_history_currency)
    df_history_enhanced = pd.concat(currency_history_rows_enhanced, ignore_index=True)
    # Last step to tag changes in market trends from one period to the other (sorting important)
    df_history_enhanced = df_history_enhanced.sort_values(['base_currency','granularity','date'], ascending=True)
    #df_history_enhanced['market_trend_continued'] = df_history_enhanced.bull_bear.eq(df_history_enhanced.bull_bear.shift()) & df_history_enhanced.base_currency.eq(df_history_enhanced.base_currency.shift()) & df_history_enhanced.granularity.eq(df_history_enhanced.granularity.shift())
    return df_history_enhanced

def get_decimal_places(number):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Returns the number of decimals for the given number. 
    # Number can be passed as Float or String

    import decimal
    return abs(decimal.Decimal(str(number)).as_tuple().exponent)

def fire_create_order_record(doc_id, doc_data):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Creates a document in the Firestore database containing the given data.
    # Returns the Firestore document ID if successful and else, the error

    import firebase_admin
    from firebase_admin import firestore
    FIRESTORE_COLLECTION_NAME = 'coinbase-orders'
    db = firestore.client()
    try:
        #ref = db.collection(FIRESTORE_COLLECTION_NAME).document()
        ref = db.collection(FIRESTORE_COLLECTION_NAME).document(doc_id)
        ref.set(doc_data, merge=True)
        return ref.id
    except Exception as e:
        return e

def fire_get_orders_wo_sell_order_id():

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Returns all orders with an empty sell_order_id from Firestore

    import firebase_admin
    from firebase_admin import firestore
    FIRESTORE_COLLECTION_NAME = 'coinbase-orders'
    db = firestore.client()
    docs = db.collection(FIRESTORE_COLLECTION_NAME).where(u'sell_order_id', u'==', u'').stream()
    return docs

def get_trading_view_signals(trading_view_symbols):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Returns a pandas dataframe with 1-minute buy/sell signal from the trading view website 
    # for each chosen crypto currency passed in variable trading_view_symbols. One row in
    # dataframe equals one crypto currency. 

    from tradingview_ta import TA_Handler, Interval
    import pandas as pd
    trading_view_rows = []
    for symbol in trading_view_symbols:
        analysis = TA_Handler(
            symbol=symbol[2],
            screener="crypto",
            exchange=symbol[1],
            interval=Interval.INTERVAL_1_MINUTE).get_analysis()
        row_data = [symbol[0],analysis.summary["RECOMMENDATION"]]
        trading_view_rows.append(row_data)

    df_trading_view_info = pd.DataFrame(trading_view_rows, columns = ['currency',
                                                                    '1min_recommendation'])
    df_trading_view_info.set_index('currency', inplace=True)
    return df_trading_view_info

def make_investment_decision():

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Will initiate a market buy for a currency in case the following criteria are met:
    # - the trading signal is BUY or STRONG_BUY
    # - the current price is below the lower Bollinger Band
    # - no buy trade has been completed in the last BOT_ONE_IDLE_HOURS_BEFORE_NEXT_PURCHASE hours 

    import pandas as pd
    import os
    import json
    IDLE_HOURS_BEFORE_NEXT_PURCHASE = float(os.environ.get('BOT_ONE_IDLE_HOURS_BEFORE_NEXT_PURCHASE'))
    BOLLINGER_LOW_INVEST_EUR = float(os.environ.get('BOT_ONE_INVEST_EUR') or 0)
    MY_CRYPTO_CURRENCIES = json.loads(os.environ['BOT_ONE_CRYPTO_CURRENCIES'])
    MY_QUOTE_CURRENCY = os.environ.get('QUOTE_CURRENCY')
    TRADING_VIEW_SYMBOLS = json.loads(os.environ['TRADING_VIEW_SYMBOLS'])
    df_historic_data = cb_get_enhanced_history(MY_QUOTE_CURRENCY, MY_CRYPTO_CURRENCIES)
    df_historic_data = df_historic_data.sort_values(['date'], ascending=True) #oldest to newest
    df_trading_view_signals = get_trading_view_signals(TRADING_VIEW_SYMBOLS)
    df_24hstats = cb_get_24h_data(MY_QUOTE_CURRENCY, MY_CRYPTO_CURRENCIES)
    server_time_now = cb_get_server_time()
    order_results = []
    for currency in MY_CRYPTO_CURRENCIES:
        product_id = currency+'-'+MY_QUOTE_CURRENCY
        current_value = df_24hstats.loc[currency]['last']
        trading_view_recommendation = df_trading_view_signals.loc[currency]['1min_recommendation']
        bb_low = df_historic_data.query('granularity == \'DAILY\' and base_currency == @currency').tail(1)['bb_low'].iloc[0]
        last_buy_fill_date = cb_get_last_buy_fill_date(product_id)
        idle_hours_reached = True
        if last_buy_fill_date is not None:
            last_fill_delta = ((server_time_now - last_buy_fill_date).days*86400 + (server_time_now - last_buy_fill_date).seconds)/3600
            if (last_fill_delta < IDLE_HOURS_BEFORE_NEXT_PURCHASE):
                idle_hours_reached = False
        if (current_value < bb_low and idle_hours_reached and (trading_view_recommendation == 'BUY' or trading_view_recommendation == 'STRONG_BUY')):
            order_id = cb_create_market_order(product_id=product_id, quote_size=BOLLINGER_LOW_INVEST_EUR)
            fire_doc_id = fire_create_order_record(doc_id=order_id,doc_data={'buy_order_id': order_id, 'bb_low': bb_low, 'trading_view_recommendation': trading_view_recommendation, 'sell_order_id': ''})
            order_results.append(f'Order now: {product_id}, price: {current_value}{MY_QUOTE_CURRENCY}, amount: {BOLLINGER_LOW_INVEST_EUR}{MY_QUOTE_CURRENCY} and order id {order_id} and Firestore doc id {fire_doc_id}')
        else:
            order_results.append(f'No order placed for {currency}; current value: {current_value}{MY_QUOTE_CURRENCY}; bb low: {bb_low}{MY_QUOTE_CURRENCY}; signal: {trading_view_recommendation}; last trade was on {last_buy_fill_date} ({idle_hours_reached})')
    return pd.DataFrame(order_results)

def place_sell_orders():

    # Version: 1.00
    # Last Updated: Feb-06-2023
     
    # Scans through all buy orders in Firestore that do not yet have a sales_order_id.
    # For each buy order during that timeframe, a stop sell order is created that will achieve
    # the defined target margin. 

    import pandas as pd
    from datetime import datetime
    import os
    TARGET_MARGIN_PERCENTAGE = float(os.environ.get('BOT_ONE_TARGET_MARGIN_PERCENTAGE'))
    docs = fire_get_orders_wo_sell_order_id()
    order_results = []
    for doc in docs:

        # 1. Add missing data from filled buy orders (since data was not available when document was created)
        #print(f'{doc.id} => {doc.to_dict()}')
        buy_order_id = doc.to_dict()['buy_order_id']
        filled_order= cb_get_aggregated_fills(order_id=buy_order_id).iloc[0]
        buy_order_id = filled_order['order_id']
        date = filled_order['date']
        product_id = filled_order['product_id']
        base_currency = filled_order['product_id'].split('-')[0]
        quote_currency = filled_order['product_id'].split('-')[1]
        buy_base_price = filled_order['price']
        buy_base_size = filled_order['size'] / filled_order['price']
        buy_quote_size = filled_order['size']
        buy_quote_commission = filled_order['commission']
        buy_quote_total_size = filled_order['total_price']
        order_data = {'buy_date': date,
            'buy_order_id': buy_order_id,
            'product_id': product_id,
            'base_currency': base_currency, 
            'quote_currency': quote_currency,
            'buy_base_price': buy_base_price,
            'buy_base_size': buy_base_size,
            'buy_quote_size': buy_quote_size,
            'buy_quote_commission': buy_quote_commission,
            'buy_quote_total_size': buy_quote_total_size,
            'sell_order_id': ''}
        fire_doc_id = fire_create_order_record(doc_id = buy_order_id, doc_data = order_data)
        
        # 2. Initiate Stop Limit sell order with respective targeet margin: 
        base_increment = cb_get_product_info(product_id)['base_increment']
        base_decimals = get_decimal_places(base_increment)
        quote_increment = cb_get_product_info(product_id)['quote_increment']
        quote_decimals = get_decimal_places(quote_increment)
        target_price = round(buy_base_price * (1 + TARGET_MARGIN_PERCENTAGE/100), quote_decimals)
        buy_base_size = round(buy_base_size, base_decimals)
        sell_order_id = cb_create_stop_limit_sell_order(product_id=product_id,base_size=buy_base_size,stop_price=target_price,limit_price=target_price)
        
        # 3. Update Firestore document with sell order data:
        fire_doc_id = fire_create_order_record(doc_id=buy_order_id,doc_data={'sell_order_id': sell_order_id,
            'sell_base_target_price': target_price,
            'sell_order_created_at': datetime.now(),
            'target_margin': TARGET_MARGIN_PERCENTAGE/100})
        order_results.append(f'Stop limit sell order {sell_order_id} for equivalent market buy order {buy_order_id} created with target price {target_price}{quote_currency} (target margin: {TARGET_MARGIN_PERCENTAGE}%); Firestore document updated ({fire_doc_id})')
    return pd.DataFrame(order_results)

def cb_create_market_order(product_id, quote_size):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Creates a market buy order for the given product_id (e.g. BTC-USD)
    # It will invest the amount of quote_size for this order (e.g. 100 USD)

    import uuid
    import json
    client_order_id = uuid.uuid4()
    url_path = '/api/v3/brokerage/orders'
    payload = {
        'product_id': product_id,
        'client_order_id': str(client_order_id),
        'side': 'BUY',
        'type': 'MARKET',
        'order_configuration': {
            'market_market_ioc': {
                'quote_size': str(quote_size)
            }
        }
    }
    try:
        response = cb_auth_post_connect(url_path=url_path, body=payload)
        json_orders = json.loads(response.text)
        order_id = json_orders['order_id']
        return order_id
    except Exception as e:
        return e

def cb_create_stop_limit_sell_order(product_id, base_size, stop_price, limit_price):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # Creates a stop limit sell order for the given product_id (e.g. BTC-USD)
    # It will spend the amount given in base_size (e.g. 0.01 BTC)

    import uuid
    import json
    client_order_id = uuid.uuid4()
    url_path = '/api/v3/brokerage/orders'
    payload = {
        'product_id': product_id,
        'client_order_id': str(client_order_id),
        'side': 'SELL',
        'order_configuration': {
            'stop_limit_stop_limit_gtc': {
                'base_size': str(base_size),
                'stop_price': str(stop_price),
                'limit_price': str(limit_price),
                'stop_direction': 'STOP_DIRECTION_STOP_UP'
            }
        }
    }
    try:
        response = cb_auth_post_connect(url_path=url_path, body=payload)
        json_orders = json.loads(response.text)
        order_id = json_orders['order_id']
        return order_id
    except Exception as e:
        return e

def investment_bot(request):

    # Version: 1.00
    # Last Updated: Feb-06-2023

    # The main function that is invoked on GCP. It connects to coinbase via authentication using
    # the provided API key and secret. 

    # make_investment_decision(): It then loads historic data for all chosen crypto currencies.
    # It then checks if buy conditions are met per defined currency. In case a buy
    # condition is met, a market order will be issued. A record is created in Firestore for each 
    # market order buy.

    # place_sell_orders(): It will then check in Firestore which purchase orders do not yet have a
    # an order id for the sales operation. For those market orders, an equivalent sales order will
    # be created in coinbase taking into consideration the defined target margin. 

    df_buy_order_results = make_investment_decision()
    df_sell_order_results = place_sell_orders()
    return df_buy_order_results.to_json(orient='index')+df_sell_order_results.to_json(orient='index') , 200