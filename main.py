import json  
import openai  
import pandas  
import matplotlib.pyplot as plt  
import streamlit as st  
import yfinance as yf  

openai.api_key = open('api_key', 'r').read()  # loading openai api key from a file

# function to fetch latest stock price given a ticker symbol
def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1].Close)

# function to calculate simple moving average (sma) for a stock
def calculate_sma(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])

# function to calculate exponential moving average (ema) for a stock
def calculate_ema(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])

# function to calculate relative strength index (rsi) for a stock
def calculate_rsi(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=14-1, adjust=False).mean()
    ema_down = down.ewm(com=14-1, adjust=False).mean()
    rs = ema_up / ema_down
    return str(100 - (100 / (1 + rs)).iloc[-1])

# function to calculate moving average convergence divergence (macd) for a stock
def calculate_macd(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    short_ema = data.ewm(span=12, adjust=False).mean()
    long_ema = data.ewm(span=26, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_histogram = macd - signal

    return f"{macd[-1]}, {signal[-1]}, {macd_histogram[-1]}"

# function to plot stock price over the last year
def plot_stock_price(ticker):   
    data = yf.Ticker(ticker).history(period='1y').Close
    plt.figure(figsize=(10, 5))  # set up figure size for the plot
    plt.plot(data.index, data.Close)  # plot the stock price data
    plt.title(f'{ticker} stock price over last year')  # set plot title
    plt.xlabel('date')  # set label for x-axis
    plt.ylabel('stock price')  # set label for y-axis
    plt.grid(True)  # show grid lines
    plt.savefig('stock.png')  # save the plot as an image
    plt.close()  # close the plot to free up memory

# all the functions above are formulae and dont need to be memorized as such, one google search away.

# list of function details for displaying in the ui
functions = [
    {
        'name': 'get_stock_price',
        'description': 'gets the latest stock price given the ticker symbol of a company.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company (aapl for apple). note : fb is renamed to meta.'
                }
            },
            'required': ['ticker']
        }
    },
    {
        'name': 'calculate_sma',
        'description': 'calculate the simple moving average for a given stock ticker and a window.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company (aapl for apple). note : fb is renamed to meta.'
                },
                'window': {
                    'type': 'integer',
                    'description': 'the timeframe to consider when calculating sma'
                }
            },
            'required': ['ticker', 'window'],
        },
    },
    {
        'name': 'calculate_ema',
        'description': 'calculate the exponential moving average for a given stock ticker and a window.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company (aapl for apple). note : fb is renamed to meta.',
                },
                'window': {
                    'type': 'integer',
                    'description': 'the timeframe to consider when calculating the ema'
                }
            },
            'required': ['ticker', 'window'],
        },
    },
    {
        'name': 'calculate_rsi',
        'description': 'calculate the rsi for a given stock ticker.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company (aapl for apple). note : fb is renamed to meta.',
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'calculate_macd',
        'description': 'calculate the macd for a given stock ticker.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company (aapl for apple). note : fb is renamed to meta.',
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'plot_stock_price',
        'description': 'plot the stock price for the last year given the ticker symbol of a company.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'the stock ticker symbol for a company (aapl for apple). note : fb is renamed to meta.',
                },
            },
            'required': ['ticker'],
        },
    },
]

# dictionary of available functions for easy function call
available_functions = {
    'get_stock_price': get_stock_price,
    'calculate_sma': calculate_sma,
    'calculate_ema': calculate_ema,
    'calculate_rsi': calculate_rsi,
    'calculate_macd': calculate_macd,
    'plot_stock_price': plot_stock_price
}

# initializing session state to store messages in the app
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# setting up streamlit app title
st.title('stocksage')

# taking user input for commands
user_input = st.text_input('your input:')

# if user input exists, process the command
if user_input:
    try:
        # appending user input to session messages
        st.session_state['messages'].append({'role': 'user', 'content': f'{user_input}'})
        # sending user input and session messages to gpt
        response = openai.chatcompletion.create(
            model='gpt-3.5-turbo',
            messages=st.session_state['messages'],
            functions=functions,
            function_call='auto'
        )

        # getting the response message from the model
        response_message = response['choices'][0]['message']

        # if the response contains a function call, execute the function and respond
        if response_message.get('function_call'):
            function_name = response_message['function_call']['name']
            function_args = json.loads(response_message['function_call']['arguments'])
            # setting arguments for the function based on its name
            if function_name in ['get_stock_price', 'calculate_rsi', 'calculate_macd', 'plot_stock_price']:
                args_dict = {'ticker': function_args.get('ticker')}
            else:
                args_dict = {'ticker': function_args.get('ticker'), 'window': function_args.get('window')}

            # calling the appropriate function based on function name
            function_to_call = available_functions[function_name]
            function_response = function_to_call(**args_dict)

            # display the plot
            if function_name == 'plot_stock_price':
                st.image('stock.png')
            else:
                # appending function response and role to session messages
                st.session_state['messages'].append(response_message)
                st.session_state['messages'].append(
                    {
                        'role': 'function',
                        'name': 'function_name',
                        'content': 'function_response'
                    }
                )
                # sending updated session messages to gpt for further processing
                second_response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=st.session_state['messages']
                )
                # displaying the response from gpt
                st.text(second_response['choices'][0]['message']['content'])
                # appending assistant response to session messages
                st.session_state['messages'].append({'role': 'assistant', 'content': second_response['choices'][0]['message']['content']})

    except Exception as e:
        st.error(f'error: {e}')

# debugging helper for me
st.session_state['messages']
