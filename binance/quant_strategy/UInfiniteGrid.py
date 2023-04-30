import time
import logging
from binance.client import Client
from decimal import Decimal, ROUND_DOWN

# 配置日志，将每一个子程序运行的日志保存为InfiniteGrid.log文件
logging.basicConfig(filename='/InfiniteGrid.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',encoding='utf-8')
logger = logging.getLogger()

# 初始化API连接
API_KEY = 'YOU_API_KEY'
API_SECRET = 'YOU_API_SECRET'
client = Client(API_KEY, API_SECRET)

# 设置交易参数
symbol = "BNBUSDT"  # 选择交易对
# 获取USDT余额
balances = client.futures_account_balance()
for balance in balances:
    if balance['asset'] == 'USDT':
        usdt_balance = float(balance['withdrawAvailable'])
        logger.info(f"USDT余额: {usdt_balance}")
leverage = 10  # 设置杠杆大小
# 设置杠杆
client.futures_change_leverage(symbol=symbol, leverage=leverage)

grid_size = 0.001  # 设置网格间距

# 设置做多做空方向状态 0表示做空 1表示做多
grid_status = 0  # 初始状态为做多

# 设置初始开仓价格，开仓价格为0表示使用最新市场价
entry_price = 0
# 网格单边下单数量
grid_count = 5 
# 获取交易规则
exchange_info = client.futures_exchange_info()
symbol_info = None
for s in exchange_info['symbols']:
    if s['symbol'] == symbol:
        symbol_info = s
        # print(symbol_info)
        break
 # 最小价格变动单位（tick size）
tick_size = float(symbol_info['filters'][0]['tickSize'])   

# 设置精度
# 开仓精度
# 
quantity_precision = symbol_info['quantityPrecision']
# logger.info(f"开仓精度:{quantity_precision}")
# 价格精度
price_precision = symbol_info['pricePrecision']
# COIN符号
coin = symbol_info['baseAsset']
# logger.info(f"价格精度:{quantity_precision}")
# 最小下单数量
min_qty = float(symbol_info['filters'][5]['notional'])
# 当前价格
ticker = client.futures_symbol_ticker(symbol=symbol)
current_price = float(ticker['price'])
# logger.info(f"当前价格: {current_price}")
# 设置USDT初始余额
usdt_balance_status = 1500
# 设置COIN初始余额
coin_balance_status = round((usdt_balance_status / current_price),price_precision)
# logger.info(f"{coin}初始余额: {coin_balance_status}")
# USDT设置初始仓位
usdt_position_size = 30
# COIN设置初始仓位
position_size = round(( usdt_position_size / current_price),quantity_precision)# 初始仓位为0.01张
# logger.info(position_size)
# USDT设置网格仓位
usdt_grid_spacing = 10
# COIN设置网格加仓数量
grid_spacing = round(usdt_grid_spacing / current_price * (usdt_balance / usdt_balance_status),quantity_precision) # 每个网格的加仓数量为3个网格间距
logger.info(grid_spacing)

# 实现交易策略
# 获取多做空方向状态 0表示做空 1表示做多
# 获取开仓初始价格,开仓价格为0表示使用最新市场价,如果开仓初始价不为0时以设置的委托价开仓
# 开仓成功后，跳出初始开仓操作
    # 如果初始开仓价格为0，则以当前市价开仓为初始仓位
if grid_status == 1:   
    if entry_price == 0:
        ticker = client.futures_symbol_ticker(symbol=symbol)
        entry_price = float(ticker['price'])
        logger.info(f"初始开多仓价格为0，以当前市价{entry_price}开仓")
        
        try:
            order = client.futures_create_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',
                quantity=position_size
            )
            logger.info(f"初始开多仓成功，订单号为{order['orderId']}")
        except Exception as e:
            logger.warning(f"初始开多仓失败，错误信息为{e}")
            
elif grid_status == 0:
    if entry_price == 0: 
        ticker = client.futures_symbol_ticker(symbol=symbol)
        entry_price = float(ticker['price'])
        logger.info(f"初始开空仓价格为0，以当前市价{entry_price}开仓")
        
        try:
            order = client.futures_create_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',
                quantity=position_size
            )
            logger.info(f"初始开空仓成功，订单号为{order['orderId']}")
        except Exception as e:
            logger.warning(f"初始开空仓失败，错误信息为{e}")# 开始加入网格模式，加入网格后不能再次加入或删除网           
# 循环执行以下操作
while True:
    try:
        order_filled = False  # 添加一个标记来表示订单是否已成交
        while True:
            # 获取历史最新成交价
            orders = client.futures_get_all_orders(symbol=symbol)       
            filled_orders = [order for order in orders if order['status'] == 'FILLED']
            latest_filled_order = max(filled_orders, key=lambda x: x['updateTime'], default=None)
            if latest_filled_order:
                entry_price = float(latest_filled_order['avgPrice'])
                logger.info(f"获取历史最新成交价为{entry_price}")
                # 撤销所有未成交的订单
                open_orders = [order for order in orders if order['status'] == 'NEW']
                for open_order in open_orders:
                    client.futures_cancel_order(symbol=symbol, orderId=open_order['orderId'])   

            # 以历史最新成交价计算下一个网格的委托价 
            if grid_status == 1:
                # 做多加仓
                next_price = round(entry_price * (1 - grid_size),quantity_precision)
                order_ids = []
                for i in range(grid_count):
                    try:
                        order_price = round(next_price - i * grid_size * entry_price, quantity_precision)
                        logger.info(f"做多加仓网格，价格为{order_price}")

                        order = client.futures_create_order(
                            symbol=symbol,
                            side='BUY',
                            type='LIMIT',
                            timeInForce='GTC',
                            quantity=grid_spacing,
                            price=order_price
                        )
                        order_ids.append(order['orderId'])  # 将订单ID保存到order_ids列表中
                        logger.info(f"做多加仓订单{order_ids}")
                        logger.info(f"做多网格加仓下单成功，订单号为{order['orderId']}")
                    except Exception as e:
                        logger.warning(f"做多网格加仓下单失败，错误信息为{e}")
                        continue  # 如果下单失败，直接跳过本次循环

        
                # next_price = round((next_price - grid_size * entry_price),quantity_precision)
                # 做多减仓
                next_price = round(entry_price * (1 + grid_size),quantity_precision)
                order_ids = []
                for i in range(grid_count):
                    try:
                        order_price = round(next_price + i * grid_size * entry_price, quantity_precision)
                        logger.info(f"做多减仓网格，价格为{order_price}")

                        order = client.futures_create_order(
                            symbol=symbol,
                            side='SELL',
                            type='LIMIT',
                            timeInForce='GTC',
                            quantity=grid_spacing,
                            price=order_price
                        )
                        order_ids.append(order['orderId'])  # 将订单ID保存到order_ids列表中
                        logger.info(f"做多减仓订单{order_ids}")
                        logger.info(f"做多网格减仓下单成功，订单号为{order['orderId']}")
                    except Exception as e:
                        logger.warning(f"做多网格减仓下单失败，错误信息为{e}")
                        continue  # 如果下单失败，直接跳过本次循环
                # 等待订单成交
                order_filled = False
                while not order_filled:
                    orders = client.futures_get_all_orders(symbol=symbol)
                    filled_orders = [order for order in orders if order['status'] == 'FILLED']
                    latest_filled_order = max(filled_orders, key=lambda x: x['updateTime'], default=None)
                    if latest_filled_order:
                        new_entry_price = float(latest_filled_order['avgPrice'])
                        if new_entry_price != entry_price:
                            order_filled = True
                            logger.info(f"订单已成交，新的成交价为{new_entry_price}")
                    time.sleep(10)  # 每隔5秒查询一次订单状态        

            elif grid_status == 0:
                # 做空加仓
                next_price = round(entry_price * (1 + grid_size),quantity_precision)
                order_ids = []
                for i in range(grid_count):
                    try:
                        order_price = round(next_price + i * grid_size * entry_price, quantity_precision)
                        logger.info(f"做空加仓网格，价格为{order_price}")
                        order = client.futures_create_order(
                            symbol=symbol,
                            side='SELL',
                            type='LIMIT',
                            timeInForce='GTC',
                            quantity=grid_spacing,
                            price=order_price
                        )
                        order_ids.append(order['orderId'])  # 将订单ID保存到order_ids列表中
                        logger.info(f"做空加仓订单{order_ids}")
                        logger.info(f"做空网格加仓下单成功，订单号为{order['orderId']}")
                    except Exception as e:
                        logger.warning(f"做空网格加仓下单失败，错误信息为{e}")
                        continue  # 如果下单失败，直接跳过本次循环
                # next_price = round((next_price + grid_size * entry_price),quantity_precision)
                # 做空减仓
                next_price = round(entry_price * (1 - grid_size),quantity_precision)
                order_ids = []
                for i in range(grid_count):
                    try:
                        order_price = round(next_price - i * grid_size * entry_price, quantity_precision)
                        logger.info(f"做空减仓网格，价格为{order_price}")
                        order = client.futures_create_order(
                            symbol=symbol,
                            side='BUY',
                            type='LIMIT',
                            timeInForce='GTC',
                            quantity=grid_spacing,
                            price=order_price
                        )
                        order_ids.append(order['orderId'])  # 将订单ID保存到order_ids列表中
                        logger.info(f"做空减仓订单{order_ids}")
                        logger.info(f"做空网格减仓下单成功，订单号为{order['orderId']}")
                    except Exception as e:
                        logger.warning(f"做空网格减仓下单失败，错误信息为{e}")
                        continue  # 如果下单失败，直接跳过本次循环
                    # next_price = round((next_price - grid_size * entry_price),quantity_precision)
                # 等待订单成交
                order_filled = False
                while not order_filled:
                    orders = client.futures_get_all_orders(symbol=symbol)
                    filled_orders = [order for order in orders if order['status'] == 'FILLED']
                    latest_filled_order = max(filled_orders, key=lambda x: x['updateTime'], default=None)
                    if latest_filled_order:
                        new_entry_price = float(latest_filled_order['avgPrice'])
                        if new_entry_price != entry_price:
                            order_filled = True
                            logger.info(f"订单已成交，新的成交价为{new_entry_price}")

                    time.sleep(10)  # 每隔5秒查询一次订单状态
            time.sleep(15)        

    except Exception as e:
        logger.error(f"程序运行出错: {e}")
    time.sleep(30)
