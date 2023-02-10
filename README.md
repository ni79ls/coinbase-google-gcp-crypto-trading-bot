# How to Restore the GCP Investment Bot Project

This is a crypto trading bot that runs on Google Cloud Platform (GCP) including an interface to Coinbase and Trading View. An in-depth article is available on [Medium]() to further explain the architecture and mechanisms of this trading bot. To fully restore the project after the download from github, you need to take the following actions:

## 1. Setup Virtual Python Environment

**Remark:** The project has been tested on a Macbook Apple Silicone chip using Python version 3.7 but it should also work on all other machines and operating systems.

First, you need to create a virtual Python environment within the root of this project folder via the follow command:

````
python3 -m venv venv
````

Before you issue this command, check the python version that you will use to setup the environment. As of writing, Google Cloud Platform uses Python 3.7. In case, there is still another environment (e.g. conda base active), you need to kill this environmen via the following command:

````
conda deactivate
````

or for non Conda environments:

````
deactivate
````

Next, you need to activate the newly created environment:

````
source venv/bin/activate
````

Now that the virtual environment is active, install all packages specified in the file `requirements.txt`:

````
pip install -r requirements.txt 
````

In case the installer hangs, try this command as root user:

````
sudo pip3 install -r requirements.txt
````

## 2. Create Environment Variables

### Local Environment Variables

Create a new file called `.env` in the root directory of this project. The file holds the following environment variables (replace the quote currency with your local currency and replace the crypto currencies with the ones you want to trade). The file content should look something like this:

````
export QUOTE_CURRENCY=EUR
export BOT_ONE_CRYPTO_CURRENCIES='["BTC","ETH","DOGE","AVAX"]'
export TRADING_VIEW_SYMBOLS='[["SUSHI","KRAKEN","SUSHIEUR"],["XTZ","KRAKEN","XTZUSD"],["AXS","BINANCE","AXSUSDT"],["BTC","COINBASE","BTCEUR"],["ETH","BITFINEX","ETHF0USTF0"],["LTC","COINBASE","LTCUSD"],["SOL","HITBTC","SOLUSD"],["AVAX","KUCOIN","AVAXUSDT"],["MANA","HITBTC","MANAUSDT"],["LINK","BINANCE","LINKUSDT"],["1INCH","KUCOIN","1INCHUSDT"],["DOGE","COINBASE","DOGEUSDT"]]'
export GOOGLE_APPLICATION_CREDENTIALS=./../google-firebase-credentials.json
export API_KEY=<your-personal-coinbase-api-key>
export API_SECRET=<your-personal-coinbase-api-secret>
export BOT_ONE_INVEST_EUR='100.00'
export BOT_ONE_IDLE_HOURS_BEFORE_NEXT_PURCHASE='24'
export BOT_ONE_TARGET_MARGIN_PERCENTAGE='14.0'
````

Remark: This file is only needed for testing the software on your local machine via Flask. 

### GCP Environment Variables

In case it does not exist, create a new file `./investment-bot/.env.yaml` with the following content:

````
QUOTE_CURRENCY: EUR
BOT_ONE_CRYPTO_CURRENCIES: '["BTC","ETH","DOGE","AVAX"]'
TRADING_VIEW_SYMBOLS: '[["SUSHI","KRAKEN","SUSHIEUR"],["XTZ","KRAKEN","XTZUSD"],["AXS","BINANCE","AXSUSDT"],["BTC","COINBASE","BTCEUR"],["ETH","BITFINEX","ETHF0USTF0"],["LTC","COINBASE","LTCUSD"],["SOL","HITBTC","SOLUSD"],["AVAX","KUCOIN","AVAXUSDT"],["MANA","HITBTC","MANAUSDT"],["LINK","BINANCE","LINKUSDT"],["1INCH","KUCOIN","1INCHUSDT"],["DOGE","COINBASE","DOGEUSDT"]]'
BOT_ONE_INVEST_EUR: '100.00'
BOT_ONE_IDLE_HOURS_BEFORE_NEXT_PURCHASE: '24'
BOT_ONE_TARGET_MARGIN_PERCENTAGE: '14.0'
````

**Remark:** The Coinbase API key and API secret should never be part of the environment variables uploaded to the server. Instead, you need to create three separate secrets in the GCP Secret Manager (see one of the upcoming steps).

## 3. Test Function Locally

To test the cloud function on your local machine, you must make the environment variables from the .env file available to your virtual Python environment by running:

````
export $(grep -v '^#' .env | xargs)
````

or

````
source .env
````

Once the environment variables are known to the shell, run the following command from the scheduler folder ./scheduler:

````
functions-framework --target=investment_bot --debug
````

This will start the internal Flask server that comes with the Functions Framework. You can then execute the function via the URL given as an output when running above command, e.g. [http://127.0.0.1:8080](http://127.0.0.1:8080)

**Important Remark:** In case the Firestore credentials do not yet exist, you need to follow **step 4b** first. 

## 4a. Create GCP Service Account

Create a new GCP Service Account that will be used by the bot function(s) and the secrets (created in next step). You have to create a special Service Account for each function (you could for instance call it `investment-bot`). Service Accounts are created in the `IAM / Service Accounts` screen. After creating the Service Account, assign the following role / project permissions on the `IAM > Grant Access` screen:
- `Cloud Functions Invoker`
- `Firebase Admin SDK Administrator Service Agent`

## 4b. Create GCP Service Account

This step is only needed to locally test the Firestore connection and create / update Firestore documents. Create another GCP Service Account (name could be `firebase-admin`) on the `IAM > Service Accounts` screen. Generate an API key from this new GCP Service Account so that it can be used by our functions in this project locally. Store the generated token file in the root folder of this project as `./google-firebase-credentials.json`. Then assign the following role / project permissions on the `IAM > Grant Access` screen for this Service Account: `Firebase Admin SDK Administrator Service Agent`.

**Remark:** This Service Account is not relevant once the function is deployet to GCP. But it is necessary to test the Firestore functionality locally. Also, the generated json is not uploaded to GCP later on since GCP automatically connects to a Firestore database that is part of the same project as the cloud functions.  

## 5. Create Secrets and Associate to Service Account

You need to create the following secrets in the GCP `Secrets / Secret Manager` (of course, you could also choose other names):

- coinbase-cloud-api-key
- coinbase-cloud-api-secret
- sendgrid-api-key

For each secret, you need to assign the Service Account created in the previous step 4b.  You need to set the permission for each of the secrets to this newly created Service Account as `Secret Manager Secret Accessor`. 

## 6. Deploy to Google GCP

Run the following command from the `./investment-bot` folder (or one of the other folders for the other functions):

````
gcloud functions deploy investment-bot --runtime python37 --trigger-http --env-vars-file .env.yaml
````

Remark: There might be an error that Cloud Build API has to be enabled first for the project. 

It will take a few minutes and your function should be available on GCP.

## 7. Set Function Secrets and Security

### Secrets

All secrets that have been created above must be added to the function as environment variables. They should map to the following environment variable names in the `.env` file and therefore the name that you use in `main.py` to retrieve those variables:

- coinbase-cloud-api-key -> API-KEY
- coinbase-cloud-api-secret -> API-SECRET

To add the secrets to the function, open the function and go into edit mode. Under `Runtime, build, connections and security settings`, you need to add all secrets and expose them as environment variables. 

### Runtime Service Account

As the `Runtime Service Account`, select the Service Account that you have created above. Also, go into the function again and under Permissions, you need to add the earlier created Service Account to have `Cloud Functions Invoker` permission on this function as well.

## 8. Schedule Function on GCP

Finally, we want our function to execute every 5 minutes (or any other regular interval). Open the `Cloud Scheduler` dashboard in GCP and create a new job. This job must contain the following key information:

- OICD as an authorization option
- Service Account from above
- The URL is the URl of the function
- Schedule in unix-cron format

Here is the unix-cron format example for a five minute interval:

````
*/5 * * * *
````

There is a great tutorial to set up a Cloud Scheduler job [here](https://cloud.google.com/community/tutorials/using-scheduler-invoke-private-functions-oidc).


